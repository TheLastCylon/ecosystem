#pragma once

#include <memory>
#include <string>
#include <unordered_map>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "otlp_tracing_middleware.hpp"
#include "middleware/buffered_middleware_base.hpp"
#include "data_transfer_objects/request_dto.hpp"
#include "data_transfer_objects/span_key.hpp"

// Mirrors ekosis_otlp_traces/buffered_middleware.py's OtlpBufferedTracingMiddleware.
// Instruments buffered endpoint processing with OTLP spans, chained to the
// routing span created by OtlpTracingMiddleware.
class OtlpBufferedTracingMiddleware : public BufferedMiddlewareBase {
public:
    explicit OtlpBufferedTracingMiddleware(std::shared_ptr<OtlpTracingMiddleware> tracing);

    asio::awaitable<nlohmann::json> before_push(
        SpanKey           span_key,
        const RequestDTO& dto) override;

    asio::awaitable<void> before_process(
        SpanKey               span_key,
        const RequestDTO&     dto,
        const nlohmann::json& metadata,
        int                   retries) override;

    asio::awaitable<void> after_process(
        SpanKey               span_key,
        const RequestDTO&     dto,
        const nlohmann::json& metadata,
        bool                  success) override;

private:
    static constexpr const char* RECEIVE_SPAN_ID_KEY = "otlp_receive_span_id";
    static constexpr const char* ROUTE_KEY_KEY        = "otlp_route_key";

    struct ProcessSpan {
        uint64_t start_unix_nano;
    };

    std::shared_ptr<OtlpTracingMiddleware>   tracing_;
    std::unordered_map<SpanKey, ProcessSpan> process_spans_;
};
