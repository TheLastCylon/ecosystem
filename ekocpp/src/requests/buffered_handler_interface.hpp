#pragma once

#include <optional>
#include <string>
#include <vector>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/span_key.hpp"

// The type-erased surface ApplicationBase's route-key registry needs --
// BufferedRequestHandler<Handler> is templated per Handler, so a
// std::unordered_map<std::string, shared_ptr<BufferedRequestHandler<???>>>
// can't exist directly; this interface is the part every instantiation has
// in common, regardless of Handler. Mirrors what
// ekosis/state_keepers/buffered_handler_keeper.py's BufferedHandlerKeeper
// actually calls on a handler -- Python gets this for free via duck typing,
// this is the explicit C++ equivalent.
class BufferedHandlerInterface {
public:
    virtual ~BufferedHandlerInterface() = default;

    virtual const std::string& route_key() const = 0;

    virtual void pause_receiving() = 0;
    virtual void unpause_receiving() = 0;
    virtual void pause_processing() = 0;
    virtual void unpause_processing() = 0;
    virtual bool is_receiving_paused() const = 0;
    virtual bool is_processing_paused() const = 0;

    virtual size_t pending_queue_size() const = 0;
    virtual size_t error_queue_size() const = 0;
    virtual void error_queue_clear() = 0;

    virtual std::vector<std::string> get_first_x_error_span_keys(size_t how_many) const = 0;
    virtual std::optional<nlohmann::json> pop_request_from_error_queue(const SpanKey& span_key) = 0;
    virtual std::optional<nlohmann::json> inspect_request_in_error_queue(const SpanKey& span_key) const = 0;

    // Moves every error-queue entry back to pending and re-kicks the
    // processing loop -- mirrors PendingQueue::move_all_error_to_pending,
    // but only BufferedRequestHandler knows it also needs to call its own
    // (private) check_process_queue() afterward.
    virtual void reprocess_error_queue() = 0;
    virtual std::optional<nlohmann::json> reprocess_error_queue_span_key(const SpanKey& span_key) = 0;

    virtual asio::awaitable<void> shut_down() = 0;
};
