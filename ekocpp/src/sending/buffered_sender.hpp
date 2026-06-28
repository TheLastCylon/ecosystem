#pragma once

#include <atomic>
#include <chrono>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <asio/any_io_executor.hpp>
#include <asio/awaitable.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/experimental/channel.hpp>
#include <asio/steady_timer.hpp>
#include <asio/use_awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../clients/client_base.hpp"
#include "../data_transfer_objects/json_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"
#include "../exceptions/exceptions.hpp"
#include "../queues/pending_queue.hpp"

class BufferedSender;

// Defined below. Free function, not a member -- same reason
// run_pending_queue_processing_loop/run_heartbeat_loop are free functions:
// a member-function coroutine's frame stores an implicit `this`, which would
// dangle if this object were destroyed while the coroutine is suspended.
asio::awaitable<void> run_send_processing_loop(std::weak_ptr<BufferedSender> weak_self);

// Mirrors ekosis/sending/{sender_base,buffered_sender_base,buffered_sender_class}.py,
// collapsed into one concrete (non-template) class -- ekocpp's DTOs are
// already schemaless nlohmann::json (see request_dto.hpp), so there's no
// Pydantic-model type parameter to carry the way Python's
// Generic[_RequestDTOType, _ResponseDTOType] does. No BufferedSenderKeeper
// either: that singleton exists in Python only because buffered_sender() is
// a decorator with no natural owner; ApplicationBase::register_buffered_sender
// IS the owner here, same simplification already applied to buffered
// endpoints (no RequestRouter-side "get_buffered_handlers()" needed either).
//
// Real contract difference from BufferedRequestHandler: a sender retries
// ONLY on ServerBusyException/CommunicationsMaxRetriesReached (the two
// failure modes that mean "try again later," not "this request is wrong")
// -- any other exception routes straight to the error queue without
// consuming a retry. The handler side's bool-return contract has no
// equivalent distinction; this one matters because ClientBase::send_message
// throws a specific typed exception per failure category, not a bare bool.
//
// Must be constructed via std::make_shared and held by shared_ptr
// (enable_shared_from_this) -- same weak_ptr/channel-based lifecycle as
// BufferedRequestHandler, reused unchanged.
class BufferedSender : public std::enable_shared_from_this<BufferedSender> {
public:
    BufferedSender(
        asio::any_io_executor        executor,
        std::shared_ptr<ClientBase>  client,
        std::string                  route_key,
        const std::string&           directory,
        const std::string&           file_basename,
        std::chrono::milliseconds    wait_period = std::chrono::milliseconds{0},
        int                          page_size   = 100,
        int                          max_retries = 0
    ) : client_(std::move(client)),
        route_key_(std::move(route_key)),
        wait_period_(wait_period),
        max_retries_(max_retries),
        executor_(executor),
        queue_(directory, file_basename, page_size),
        shutdown_done_(executor_, 1) {}

    const std::string& route_key() const { return route_key_; }

    void enqueue(const nlohmann::json& data, SpanKey span_key = SpanKey::generate()) {
        queue_.push_pending(span_key, data, 0);
        check_process_send_queue();
    }

    template <JsonDTO Dto>
    void enqueue(const Dto& data, SpanKey span_key = SpanKey::generate()) {
        enqueue(data.to_json(), span_key);
    }


    void pause_send_process() { sending_paused_.store(true); }
    void unpause_send_process() { sending_paused_.store(false); check_process_send_queue(); }
    bool is_send_process_paused() const { return sending_paused_.load(); }

    size_t pending_queue_size() const { return queue_.get_pending_size(); }
    size_t error_queue_size() const { return queue_.get_error_size(); }
    void error_queue_clear() { queue_.clear_error_queue(); }

    std::vector<std::string> get_first_x_error_span_keys(size_t how_many) const {
        return queue_.get_first_x_error_span_keys(how_many);
    }

    std::optional<nlohmann::json> pop_request_from_error_queue(const SpanKey& span_key) {
        return queue_.pop_error_q_span_key(span_key);
    }

    std::optional<nlohmann::json> inspect_request_in_error_queue(const SpanKey& span_key) const {
        return queue_.inspect_error_q_span_key(span_key);
    }

    void reprocess_error_queue() {
        queue_.move_all_error_to_pending();
        check_process_send_queue();
    }

    std::optional<nlohmann::json> reprocess_error_queue_span_key(const SpanKey& span_key) {
        auto moved = queue_.move_one_error_to_pending(span_key);
        if (moved) {
            check_process_send_queue();
        }
        return moved;
    }

    // Same channel-based confirmed-exit pairing as BufferedRequestHandler::shut_down.
    asio::awaitable<void> shut_down() {
        pause_send_process();
        shutdown_requested_.store(true);

        if (!running_.load()) {
            queue_.shut_down();
            co_return;
        }
        co_await shutdown_done_.async_receive(asio::use_awaitable);
    }

private:
    friend asio::awaitable<void> run_send_processing_loop(std::weak_ptr<BufferedSender> weak_self);

    void check_process_send_queue() {
        if (!running_.exchange(true)) {
            asio::co_spawn(executor_, run_send_processing_loop(weak_from_this()), asio::detached);
        }
    }

    // Shared by both retryable-exception catch clauses in the loop below --
    // mirrors Python's single `except (ServerBusyException,
    // CommunicationsMaxRetriesReached):` tuple catch, just as two separate
    // catch blocks (the two exception types share no useful common base
    // narrower than ExceptionBase itself) calling one shared body.
    void retry_or_route_to_error(const PendingEntry& popped) {
        const int next_retries = popped.retries + 1;
        if (next_retries >= max_retries_) {
            queue_.push_error(popped.span_key, popped.data, "Max retries reached.", popped.metadata);
        } else {
            queue_.push_pending(popped.span_key, popped.data, next_retries, popped.metadata);
        }
    }

    std::shared_ptr<ClientBase> client_;
    std::string                 route_key_;
    std::chrono::milliseconds   wait_period_;
    int                         max_retries_;
    asio::any_io_executor       executor_;
    PendingQueue                queue_;

    std::atomic<bool> sending_paused_{true};
    std::atomic<bool> running_{false};
    std::atomic<bool> shutdown_requested_{false};
    asio::experimental::channel<void(std::error_code)> shutdown_done_;
};

// Free function -- see the forward declaration's comment for why. `self` is
// re-acquired fresh at the top of each iteration, same discipline as the
// other two coroutine loops, even though it's held across this loop's own
// co_await points (the wait_period timer, the actual send) within a single
// iteration -- only the TOP of the loop needs the fresh re-lock check.
inline asio::awaitable<void> run_send_processing_loop(std::weak_ptr<BufferedSender> weak_self) {
    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return; // owner is gone -- nothing left to send for.

        if (self->sending_paused_.load() || self->queue_.get_pending_size() == 0) {
            break;
        }

        auto popped = self->queue_.pop();
        if (!popped) break;

        if (self->wait_period_.count() > 0) {
            asio::steady_timer timer(self->executor_, self->wait_period_);
            co_await timer.async_wait(asio::use_awaitable);
        }

        try {
            co_await self->client_->send_message(self->route_key_, popped->data, popped->span_key);
        } catch (const ServerBusyException&) {
            self->retry_or_route_to_error(*popped);
        } catch (const CommunicationsMaxRetriesReached&) {
            self->retry_or_route_to_error(*popped);
        } catch (const std::exception& e) {
            self->queue_.push_error(popped->span_key, popped->data, e.what(), popped->metadata);
        }
    }

    auto self = weak_self.lock();
    if (!self) co_return;

    self->running_.store(false);
    if (self->shutdown_requested_.load()) {
        self->queue_.shut_down();
        self->shutdown_done_.try_send(std::error_code{});
    }
}
