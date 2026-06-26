#pragma once

#include <optional>
#include <string>

#include <nlohmann/json.hpp>
#include <spdlog/common.h>

// Mirrors ekosis/data_transfer_objects/otlp_log_record.py's OtlpLogRecord +
// severity_for_levelno(). OTel severity bands: TRACE 1-4 / DEBUG 5-8 /
// INFO 9-12 / WARN 13-16 / ERROR 17-20 / FATAL 21-24 -- both sides map onto
// the first number of each band.
//
// spdlog::level::trace -> (1, "TRACE") is a deliberate extension, not a
// divergence to chase parity away from: Python's mapping can never reach
// this case (stdlib logging has no trace level at all), but spdlog does,
// and OTel's spec defines the band -- there's a genuinely correct value to
// give here that Python's own table just never needed.
struct OtlpLogRecord {
    std::string                timestamp;
    int                        severity_number;
    std::string                severity_text;
    std::string                body;
    nlohmann::json              attributes = nlohmann::json::object();
    std::optional<std::string> trace_id;
    std::optional<std::string> span_id;

    nlohmann::json to_json() const {
        return {
            {"timestamp", timestamp},
            {"severity_number", severity_number},
            {"severity_text", severity_text},
            {"body", body},
            {"attributes", attributes},
            {"trace_id", trace_id ? nlohmann::json(*trace_id) : nlohmann::json(nullptr)},
            {"span_id", span_id ? nlohmann::json(*span_id) : nlohmann::json(nullptr)},
        };
    }
};

struct OtelSeverity {
    int         number;
    std::string text;
};

inline OtelSeverity severity_for_level(spdlog::level::level_enum level) {
    switch (level) {
        case spdlog::level::trace:    return {1, "TRACE"};
        case spdlog::level::debug:    return {5, "DEBUG"};
        case spdlog::level::info:     return {9, "INFO"};
        case spdlog::level::warn:     return {13, "WARN"};
        case spdlog::level::err:      return {17, "ERROR"};
        case spdlog::level::critical: return {21, "FATAL"};
        default:                      return {0, "UNSPECIFIED"};
    }
}
