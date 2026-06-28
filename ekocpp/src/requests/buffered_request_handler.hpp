#pragma once

#include <atomic>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <asio/any_io_executor.hpp>
#include <asio/awaitable.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/experimental/channel.hpp>
#include <asio/this_coro.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/span_key.hpp"
#include "../exceptions/exceptions.hpp"
#include "../middleware/buffered_middleware_manager.hpp"
#include "../queues/pending_queue.hpp"
#include "buffered_handler_interface.hpp"
#include "request_context.hpp"
#include "request_router.hpp" // invoke_with_context/resolve<T> -- reused, not duplicated, for the buffered-handler call path

template <typename Handler> class BufferedRequestHandler;

// Defined below. Forward-declared so it can be named in the friend
// declaration -- same reason persistent_stream_client_base.hpp forward-
// declares run_heartbeat_loop: a member-function coroutine's frame always
// stores an implicit `this`, which would dangle if this object were
// destroyed while the coroutine is suspended. The free function instead
// takes a weak_ptr by value, re-locking fresh each time it actually touches
// the object.
template <typename Handler>
asio::awaitable<void> run_pending_queue_processing_loop(std::weak_ptr<BufferedRequestHandler<Handler>> weak_self);

// Mirrors ekosis/requests/buffered_handler_base.py's BufferedRequestHandlerBase
// + buffered_handler.py's BufferedHandler -- collapsed into one class since
// C++ has no decorator-based registration step to split across (Python's
// `function` member living on a thin BufferedHandler subclass has no reason
// to be separate here).
//
// Must be constructed via std::make_shared and held by shared_ptr from that
// point on (enable_shared_from_this) -- the background processing loop
// coroutine outlives any single push() call, for the same reason
// PersistentStreamClientBase's heartbeat does. Unlike the heartbeat (one
// infinite loop spawned once at start()), this loop is spawned ON DEMAND:
// push() spawns it if not already running, and the loop itself exits once
// the pending queue drains (or processing is paused) -- a later push()
// re-spawns it. running_ is the gate, set true right before spawning and
// false right as the loop exits, both via the single io_context thread's
// cooperative scheduling (no other coroutine can observe a torn state in
// between, same assumption Python's single-threaded asyncio event loop makes).
//
// Handler contract: same SpanKey/RequestDTO& injectable-parameter convention
// as register_endpoint's handlers (resolved via the same function_traits/
// resolve<T> machinery in request_router.hpp), but MUST return bool --
// true means the buffered request succeeded and should be dropped from the
// queue, false means retry (or route to the error queue once max_retries
// is reached). This is a real contract difference from register_endpoint's
// handlers (which return the response payload), not an oversight. Also
// synchronous, like every other ekocpp handler today -- nothing currently
// needs a handler that itself co_awaits mid-processing; extend if that ever
// becomes a real need rather than building it speculatively now.
template <typename Handler>
class BufferedRequestHandler : public BufferedHandlerInterface,
                                public std::enable_shared_from_this<BufferedRequestHandler<Handler>> {
public:
    BufferedRequestHandler(
        asio::any_io_executor executor,
        std::string           route_key,
        Handler                handler,
        const std::string&    directory,
        const std::string&    file_basename,
        int                    page_size   = 100,
        int                    max_retries = 0
    ) : route_key_(std::move(route_key)),
        handler_(std::move(handler)),
        max_retries_(max_retries),
        executor_(executor),
        queue_(directory, file_basename, page_size),
        shutdown_done_(executor_, 1) {}

    const std::string& route_key() const override { return route_key_; }

    void pause_receiving() override { receiving_paused_.store(true); }
    void unpause_receiving() override { receiving_paused_.store(false); check_process_queue(); }
    void pause_processing() override { processing_paused_.store(true); }
    void unpause_processing() override { processing_paused_.store(false); check_process_queue(); }
    bool is_receiving_paused() const override { return receiving_paused_.load(); }
    bool is_processing_paused() const override { return processing_paused_.load(); }

    size_t pending_queue_size() const override { return queue_.get_pending_size(); }
    size_t error_queue_size() const override { return queue_.get_error_size(); }
    void error_queue_clear() override { queue_.clear_error_queue(); }

    std::vector<std::string> get_first_x_error_span_keys(size_t how_many) const override {
        return queue_.get_first_x_error_span_keys(how_many);
    }

    std::optional<nlohmann::json> pop_request_from_error_queue(const SpanKey& span_key) override {
        return queue_.pop_error_q_span_key(span_key);
    }

    std::optional<nlohmann::json> inspect_request_in_error_queue(const SpanKey& span_key) const override {
        return queue_.inspect_error_q_span_key(span_key);
    }

    void reprocess_error_queue() override {
        queue_.move_all_error_to_pending();
        check_process_queue();
    }

    std::optional<nlohmann::json> reprocess_error_queue_span_key(const SpanKey& span_key) override {
        auto moved = queue_.move_one_error_to_pending(span_key);
        if (moved) {
            check_process_queue();
        }
        return moved;
    }

    // Matches RequestRouter's HandlerWrapper shape exactly
    // (RequestContext& -> asio::awaitable<json>) -- register_buffered_endpoint
    // registers this straight into RequestRouter's existing route table, no
    // second dispatch path needed.
    asio::awaitable<nlohmann::json> push(RequestContext& request_context) {
        if (receiving_paused_.load()) {
            throw ServerBusyException("Receiving on '" + route_key_ + "' has been paused.");
        }
        nlohmann::json metadata = co_await BufferedMiddlewareManager::instance().collect_push_metadata(
            request_context.span_key, request_context.dto
        );
        queue_.push_pending(request_context.span_key, request_context.dto.data, 0, metadata);
        check_process_queue();
        co_return nlohmann::json{{"span_key", request_context.span_key.to_string()}};
    }

    // Pauses both flags, then waits for any in-flight processing loop
    // iteration to actually exit before flushing the queue to disk --
    // mirrors Python's shutdown()/__shut_down_check() pairing (wait for
    // `running` to go false, then queue.shut_down()), via the same
    // channel-based confirmed-exit pattern PersistentStreamClientBase uses
    // for stop().
    asio::awaitable<void> shut_down() override {
        pause_receiving();
        pause_processing();
        shutdown_requested_.store(true);

        if (!running_.load()) {
            queue_.shut_down();
            co_return;
        }
        co_await shutdown_done_.async_receive(asio::use_awaitable);
    }

private:
    friend asio::awaitable<void> run_pending_queue_processing_loop<Handler>(std::weak_ptr<BufferedRequestHandler<Handler>> weak_self);

    void check_process_queue() {
        if (!running_.exchange(true)) {
            asio::co_spawn(executor_, run_pending_queue_processing_loop<Handler>(this->weak_from_this()), asio::detached);
        }
    }

    std::string           route_key_;
    Handler                handler_;
    int                    max_retries_;
    asio::any_io_executor  executor_;
    PendingQueue           queue_;

    std::atomic<bool> receiving_paused_{true};
    std::atomic<bool> processing_paused_{true};
    std::atomic<bool> running_{false};
    std::atomic<bool> shutdown_requested_{false};
    asio::experimental::channel<void(std::error_code)> shutdown_done_;
};

// Free function, not a member -- see the friend declaration's comment above
// for why. `self` is re-acquired fresh at the top of each iteration and
// released at the end of it, same discipline as run_heartbeat_loop, even
// though nothing here currently co_awaits mid-iteration (the handler call
// and all queue ops are synchronous) -- keeps the pattern consistent in
// case a future handler ever does need to suspend mid-call.
template <typename Handler>
asio::awaitable<void> run_pending_queue_processing_loop(std::weak_ptr<BufferedRequestHandler<Handler>> weak_self) {
    using traits = function_traits<Handler>;

    for (;;) {
        auto self = weak_self.lock();
        if (!self) co_return; // owner is gone -- nothing left to process for.

        if (self->processing_paused_.load() || !self->queue_.has_pending()) {
            break;
        }

        auto popped = self->queue_.pop();
        if (!popped) break;

        co_await asio::this_coro::set_span_key(popped->span_key);

        RequestDTO     local_dto{popped->data};
        RequestContext context{popped->span_key, local_dto};
        auto&          bmm     = BufferedMiddlewareManager::instance();

        bool success = false;
        try {
            co_await bmm.run_before_process(popped->span_key, local_dto, popped->metadata, popped->retries);
            if constexpr (is_awaitable<typename traits::return_type>::value) {
                success = co_await invoke_with_context(self->handler_, context, std::make_index_sequence<traits::argument_type_list_size>{});
            } else {
                success = invoke_with_context(self->handler_, context, std::make_index_sequence<traits::argument_type_list_size>{});
            }
            co_await bmm.run_after_process(popped->span_key, local_dto, popped->metadata, success);
        } catch (const std::exception&) {
            success = false; // mirrors Python's lack of a catch here being a real bug class avoided: a handler exception now retries/errors instead of killing the loop silently.
        }

        if (!success) {
            const int next_retries = popped->retries + 1;
            if (next_retries >= self->max_retries_) {
                self->queue_.push_error(popped->span_key, popped->data, "Max retries reached.", popped->metadata);
            } else {
                self->queue_.push_pending(popped->span_key, popped->data, next_retries, popped->metadata);
            }
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
