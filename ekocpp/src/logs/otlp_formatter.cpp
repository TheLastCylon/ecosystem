#include "otlp_formatter.hpp"

#include <chrono>
#include <cstdio>
#include <ctime>

#include "../configuration/config_models.hpp"
#include "../coroutines/ambient_span_context.hpp"
#include "../data_transfer_objects/otlp_log_record.hpp"

namespace {

// Matches Python's datetime.fromtimestamp(record.created,
// tz=datetime.timezone.utc).isoformat() exactly -- e.g.
// "2026-06-23T22:25:16.878123+00:00". gmtime_r + snprintf, not <chrono>
// formatting -- same reasoning ekosis_log_shipper's otlp_envelope.cpp
// already settled on (GCC 13's libstdc++ chrono parsing/formatting support
// is incomplete; this is reliable and the timestamp is always UTC by
// construction here too).
std::string format_iso8601_utc(spdlog::log_clock::time_point time) {
    using namespace std::chrono;

    const auto   seconds_since_epoch  = time_point_cast<seconds>(time);
    const auto   microsecond_fraction = duration_cast<microseconds>(time - seconds_since_epoch).count();
    const time_t epoch_seconds        = seconds_since_epoch.time_since_epoch().count();

    std::tm tm{};
    gmtime_r(&epoch_seconds, &tm);

    char buffer[64];
    std::snprintf(buffer, sizeof(buffer), "%04d-%02d-%02dT%02d:%02d:%02d.%06lld+00:00",
        tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec,
        static_cast<long long>(microsecond_fraction));
    return buffer;
}

} // namespace

void OtlpFormatter::format(const spdlog::details::log_msg& msg, spdlog::memory_buf_t& dest) {
    const OtelSeverity     severity    = severity_for_level(msg.level);
    const SpanKey          ambient     = thread_local_span_key();
    const bool             has_span    = !(ambient == SpanKey{}); // all-zero == "never seeded", not a real span
    const AppConfiguration& app_config = AppConfiguration::instance();

    OtlpLogRecord record;
    record.timestamp       = format_iso8601_utc(msg.time);
    record.severity_number = severity.number;
    record.severity_text   = severity.text;
    record.body            = std::string(msg.payload.begin(), msg.payload.end());
    record.attributes      = {
        // application_name/instance properly belong on the OTLP Resource
        // (one per file, set from the shipper's own config at wrap-time) --
        // included here anyway, on purpose, same reasoning as Python: a
        // user with no observability stack tailing the raw file directly
        // has no other way to know which app/instance a line came from.
        {"application_name", app_config.name()},
        {"application_instance", app_config.instance_id()},
    };
    if (!msg.source.empty()) {
        record.attributes["filename"] = msg.source.filename;
        record.attributes["lineno"]   = msg.source.line;
        record.attributes["funcName"] = msg.source.funcname;
    }
    record.trace_id = has_span ? std::optional<std::string>(ambient.trace_id_hex()) : std::nullopt;
    record.span_id  = has_span ? std::optional<std::string>(ambient.span_id_hex()) : std::nullopt;

    const std::string json_line = record.to_json().dump();
    dest.append(json_line.data(), json_line.data() + json_line.size());
    dest.push_back('\n');
}

std::unique_ptr<spdlog::formatter> OtlpFormatter::clone() const {
    return std::make_unique<OtlpFormatter>();
}
