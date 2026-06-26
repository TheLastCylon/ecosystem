#pragma once

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/request_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/middleware/buffered_middleware_base.py's BufferedMiddlewareBase.
// Default implementations are no-ops.
//
// before_push: called when an item is first enqueued. Returns a metadata dict
//   (nlohmann::json object) to be stored alongside the item. Multiple
//   middlewares' metadata dicts are merged by BufferedMiddlewareManager.
//
// before_process: called immediately before the buffered handler processes
//   an item. receives the stored metadata and the retry count.
//
// after_process: called after the buffered handler returns. success=true means
//   the handler returned true; false means it returned false or threw.
class BufferedMiddlewareBase {
public:
    virtual ~BufferedMiddlewareBase() = default;

    virtual asio::awaitable<nlohmann::json> before_push(
        SpanKey           /*span_key*/,
        const RequestDTO& /*dto*/)
    {
        co_return nlohmann::json::object();
    }

    virtual asio::awaitable<void> before_process(
        SpanKey                /*span_key*/,
        const RequestDTO&      /*dto*/,
        const nlohmann::json&  /*metadata*/,
        int                    /*retries*/)
    {
        co_return;
    }

    virtual asio::awaitable<void> after_process(
        SpanKey                /*span_key*/,
        const RequestDTO&      /*dto*/,
        const nlohmann::json&  /*metadata*/,
        bool                   /*success*/)
    {
        co_return;
    }
};
