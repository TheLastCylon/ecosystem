#include "otlp_tracing_middleware.hpp"

#include <chrono>
#include <cstdio>
#include <utility>

namespace {

uint64_t now_unix_nano() {
    using namespace std::chrono;
    return static_cast<uint64_t>(
        duration_cast<nanoseconds>(system_clock::now().time_since_epoch()).count()
    );
}

std::string span_id_to_hex(uint64_t span_id) {
    char buffer[17];
    std::snprintf(buffer, sizeof(buffer), "%016llx", static_cast<unsigned long long>(span_id));
    return buffer;
}

} // namespace

OtlpTracingMiddleware::OtlpTracingMiddleware(
    const std::string& endpoint,
    const std::string& service_name)
    : exporter_(endpoint, service_name)
{}

asio::awaitable<RequestDTO> OtlpTracingMiddleware::before_routing(SpanKey span_key, RequestDTO dto) {
    active_spans_[span_key] = ActiveSpan{
        now_unix_nano(),
        SpanKey::generate().span_id,
        dto.route_key,
    };
    co_return dto;
}

asio::awaitable<nlohmann::json> OtlpTracingMiddleware::after_routing(SpanKey span_key, nlohmann::json response) {
    const auto it = active_spans_.find(span_key);
    if (it != active_spans_.end()) {
        const ActiveSpan& active = it->second;
        OtlpSpanRecord    record;
        record.trace_id        = span_key.trace_id_hex();
        record.span_id         = span_id_to_hex(active.span_id);
        record.parent_span_id  = span_key.span_id_hex();
        record.name            = active.route_key;
        record.start_unix_nano = active.start_unix_nano;
        record.end_unix_nano   = now_unix_nano();
        record.success         = true;
        record.attributes      = {
            {"request.route_key", active.route_key},
            {"request.trace_id",  span_key.trace_id_hex()},
            {"request.span_id",   span_key.span_id_hex()},
        };
        exporter_.add_span(std::move(record));
        active_spans_.erase(it);
    }
    co_return response;
}

std::optional<OtlpTracingMiddleware::ActiveSpan> OtlpTracingMiddleware::get_active_span(const SpanKey& span_key) const {
    const auto it = active_spans_.find(span_key);
    if (it == active_spans_.end()) {
        return std::nullopt;
    }
    return it->second;
}

void OtlpTracingMiddleware::emit_span(OtlpSpanRecord record) {
    exporter_.add_span(std::move(record));
}
