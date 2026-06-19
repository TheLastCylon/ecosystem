#include "otlp_envelope.hpp"

#include <ctime>
#include <cstdio>

#include <nlohmann/json.hpp>

using nlohmann::json;

namespace {

// OtlpFormatter always stamps timestamps in UTC (tz=datetime.timezone.utc),
// e.g. "2026-06-18T17:27:24.331740+00:00" -- timegm interprets the broken-
// down time as UTC directly, so no offset arithmetic is needed here.
uint64_t parse_iso8601_to_unix_nanos(const std::string& timestamp) {
    int year = 0, month = 0, day = 0, hour = 0, minute = 0, second = 0, micros = 0;
    std::sscanf(timestamp.c_str(), "%d-%d-%dT%d:%d:%d.%d",
                &year, &month, &day, &hour, &minute, &second, &micros);

    struct tm tm{};
    tm.tm_year = year - 1900;
    tm.tm_mon  = month - 1;
    tm.tm_mday = day;
    tm.tm_hour = hour;
    tm.tm_min  = minute;
    tm.tm_sec  = second;

    time_t epoch_seconds = timegm(&tm);
    return static_cast<uint64_t>(epoch_seconds) * 1'000'000'000ULL
         + static_cast<uint64_t>(micros) * 1'000ULL;
}

json attribute_kv(const std::string& key, const json& value) {
    json kv;
    kv["key"] = key;
    if (value.is_string()) {
        kv["value"]["stringValue"] = value.get<std::string>();
    } else if (value.is_number_integer()) {
        kv["value"]["intValue"] = value.get<int64_t>();
    } else if (value.is_boolean()) {
        kv["value"]["boolValue"] = value.get<bool>();
    } else {
        kv["value"]["stringValue"] = value.dump();
    }
    return kv;
}

json convert_one_record(const json& record) {
    json log_record;
    log_record["timeUnixNano"]        = std::to_string(parse_iso8601_to_unix_nanos(record.at("timestamp").get<std::string>()));
    log_record["severityNumber"]      = record.at("severity_number").get<int>();
    log_record["severityText"]        = record.at("severity_text").get<std::string>();
    log_record["body"]["stringValue"] = record.at("body").get<std::string>();

    json attributes = json::array();
    if (record.contains("attributes")) {
        for (const auto& [key, value] : record.at("attributes").items()) {
            attributes.push_back(attribute_kv(key, value));
        }
    }
    log_record["attributes"] = attributes;

    if (record.contains("trace_id") && !record.at("trace_id").is_null()) {
        log_record["traceId"] = record.at("trace_id").get<std::string>();
    }
    if (record.contains("span_id") && !record.at("span_id").is_null()) {
        log_record["spanId"] = record.at("span_id").get<std::string>();
    }
    return log_record;
}

} // namespace

// --------------------------------------------------------------------------------
ResourceInfo extract_resource_info(const std::string& json_line) {
    json         record = json::parse(json_line);
    ResourceInfo info;

    if (record.contains("attributes")) {
        const auto& attrs = record.at("attributes");
        if (attrs.contains("application_name")) {
            info.service_name = attrs.at("application_name").get<std::string>();
        }
        if (attrs.contains("application_instance")) {
            info.service_instance_id = attrs.at("application_instance").get<std::string>();
        }
    }
    return info;
}

// --------------------------------------------------------------------------------
std::string build_otlp_logs_payload(const std::vector<std::string>& json_lines, const ResourceInfo& resource) {
    json log_records = json::array();
    for (const auto& line : json_lines) {
        log_records.push_back(convert_one_record(json::parse(line)));
    }

    json payload;
    payload["resourceLogs"] = json::array({
        {
            {"resource", {
                {"attributes", json::array({
                    attribute_kv("service.name",        resource.service_name),
                    attribute_kv("service.instance.id", resource.service_instance_id),
                })}
            }},
            {"scopeLogs", json::array({
                {
                    {"scope", json::object()},
                    {"logRecords", log_records}
                }
            })}
        }
    });

    return payload.dump();
}
