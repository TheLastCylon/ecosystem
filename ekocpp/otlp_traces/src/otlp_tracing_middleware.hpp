#pragma once

#include <optional>
#include <string>
#include <unordered_map>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "otlp_span_exporter.hpp"
#include "otlp_span_record.hpp"
#include "middleware/middleware_base.hpp"
#include "data_transfer_objects/request_dto.hpp"
#include "data_transfer_objects/span_key.hpp"

// Mirrors ekosis_otlp_traces/middleware.py's OtlpTracingMiddleware.
// Wraps every routing request in an OTLP span:
//   before_routing -- records start timestamp and route_key
//   after_routing  -- records end timestamp, emits the completed span
class OtlpTracingMiddleware : public MiddlewareBase {
public:
    OtlpTracingMiddleware(const std::string& endpoint, const std::string& service_name);

    asio::awaitable<RequestDTO>     before_routing(SpanKey span_key, RequestDTO dto)         override;
    asio::awaitable<nlohmann::json> after_routing(SpanKey span_key, nlohmann::json response) override;

    // Used by OtlpBufferedTracingMiddleware::before_push to capture the
    // receive-side span_id before after_routing closes the routing span.
    struct ActiveSpan {
        uint64_t    start_unix_nano;
        uint64_t    span_id;   // freshly generated; incoming span_key.span_id becomes parent_span_id
        std::string route_key;
    };
    std::optional<ActiveSpan> get_active_span(const SpanKey& span_key) const;

    // Used by OtlpBufferedTracingMiddleware to emit process spans via the
    // shared exporter without exposing exporter_ directly.
    void emit_span(OtlpSpanRecord record);

private:
    std::unordered_map<SpanKey, ActiveSpan> active_spans_;
    OtlpSpanExporter                        exporter_;
};
