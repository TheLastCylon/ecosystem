#include "otlp_buffered_tracing_middleware.hpp"

#include <chrono>
#include <cstdio>
#include <optional>
#include <string>
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

OtlpBufferedTracingMiddleware::OtlpBufferedTracingMiddleware(
    std::shared_ptr<OtlpTracingMiddleware> tracing)
    : tracing_(std::move(tracing))
{}

asio::awaitable<nlohmann::json> OtlpBufferedTracingMiddleware::before_push(
    SpanKey           span_key,
    const RequestDTO& /*dto*/)
{
    const std::optional<OtlpTracingMiddleware::ActiveSpan> active = tracing_->get_active_span(span_key);
    if (!active) {
        co_return nlohmann::json::object();
    }
    char span_id_hex[17];
    std::snprintf(span_id_hex, sizeof(span_id_hex), "%016llx", static_cast<unsigned long long>(active->span_id));
    co_return nlohmann::json{
        {RECEIVE_SPAN_ID_KEY, std::string(span_id_hex)},
        {ROUTE_KEY_KEY,       active->route_key},
    };
}

asio::awaitable<void> OtlpBufferedTracingMiddleware::before_process(
    SpanKey               span_key,
    const RequestDTO&     /*dto*/,
    const nlohmann::json& /*metadata*/,
    int                   /*retries*/)
{
    process_spans_[span_key] = ProcessSpan{now_unix_nano()};
    co_return;
}

asio::awaitable<void> OtlpBufferedTracingMiddleware::after_process(
    SpanKey               span_key,
    const RequestDTO&     /*dto*/,
    const nlohmann::json& metadata,
    bool                  success)
{
    const auto it = process_spans_.find(span_key);
    if (it == process_spans_.end()) {
        co_return;
    }
    const std::string receive_span_id = metadata.value(RECEIVE_SPAN_ID_KEY, "");
    const std::string route_key       = metadata.value(ROUTE_KEY_KEY, "buffered");

    OtlpSpanRecord record;
    record.trace_id        = span_key.trace_id_hex();
    record.span_id         = span_id_to_hex(SpanKey::generate().span_id);
    record.parent_span_id  = receive_span_id;
    record.name            = route_key + ".process";
    record.start_unix_nano = it->second.start_unix_nano;
    record.end_unix_nano   = now_unix_nano();
    record.success         = success;
    record.attributes      = {
        {"request.trace_id", span_key.trace_id_hex()},
        {"request.span_id",  span_key.span_id_hex()},
    };
    tracing_->emit_span(std::move(record));
    process_spans_.erase(it);
    co_return;
}
