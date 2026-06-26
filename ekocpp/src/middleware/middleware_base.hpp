#pragma once

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/request_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/middleware/middleware_base.py's MiddlewareBase.
// Default implementations are pass-through coroutines.
//
// before_routing: receives the (span_key, dto) pair and returns the
//   (possibly modified) dto that will be used for the actual handler call.
//   Chain each middleware's output into the next middleware's input.
//
// after_routing: receives the (span_key, response data) pair and returns the
//   (possibly modified) response data that will be wrapped in the
//   {status, data} envelope. Called after the handler, before the envelope.
class MiddlewareBase {
public:
    virtual ~MiddlewareBase() = default;

    virtual asio::awaitable<RequestDTO> before_routing(SpanKey /*span_key*/, RequestDTO dto) {
        co_return dto;
    }

    virtual asio::awaitable<nlohmann::json> after_routing(SpanKey /*span_key*/, nlohmann::json response) {
        co_return response;
    }
};
