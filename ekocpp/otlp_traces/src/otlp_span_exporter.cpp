#include "otlp_span_exporter.hpp"

#include <chrono>
#include <string>
#include <utility>
#include <vector>

#include <curl/curl.h>
#include <nlohmann/json.hpp>

namespace {

nlohmann::json build_otlp_json(
    const std::string&                 service_name,
    const std::vector<OtlpSpanRecord>& batch)
{
    nlohmann::json spans_array = nlohmann::json::array();
    for (const OtlpSpanRecord& record : batch) {
        nlohmann::json attributes = nlohmann::json::array();
        for (const std::pair<std::string, std::string>& attr : record.attributes) {
            attributes.push_back({
                {"key",   attr.first},
                {"value", {{"stringValue", attr.second}}}
            });
        }
        nlohmann::json span = {
            {"traceId",           record.trace_id},
            {"spanId",            record.span_id},
            {"name",              record.name},
            {"kind",              2},
            {"startTimeUnixNano", std::to_string(record.start_unix_nano)},
            {"endTimeUnixNano",   std::to_string(record.end_unix_nano)},
            {"status",            {{"code", record.success ? 1 : 2}}},
            {"attributes",        attributes},
        };
        if (!record.parent_span_id.empty()) {
            span["parentSpanId"] = record.parent_span_id;
        }
        spans_array.push_back(std::move(span));
    }
    return nlohmann::json{
        {"resourceSpans", {{
            {"resource", {{"attributes", {{
                {"key",   "service.name"},
                {"value", {{"stringValue", service_name}}}
            }}}}},
            {"scopeSpans", {{
                {"scope", {{"name", "ekocpp"}}},
                {"spans", std::move(spans_array)}
            }}}
        }}}
    };
}

} // namespace

OtlpSpanExporter::OtlpSpanExporter(
    std::string endpoint,
    std::string service_name,
    int         batch_size,
    int         flush_interval_ms)
    : endpoint_(std::move(endpoint))
    , service_name_(std::move(service_name))
    , batch_size_(batch_size)
    , flush_interval_ms_(flush_interval_ms)
    , flush_thread_([this] { flush_loop(); })
{}

OtlpSpanExporter::~OtlpSpanExporter() {
    {
        std::unique_lock<std::mutex> lock(mutex_);
        shutdown_ = true;
    }
    cv_.notify_one();
    flush_thread_.join();
}

void OtlpSpanExporter::add_span(OtlpSpanRecord record) {
    bool should_notify = false;
    {
        std::unique_lock<std::mutex> lock(mutex_);
        pending_.push_back(std::move(record));
        should_notify = (static_cast<int>(pending_.size()) >= batch_size_);
    }
    if (should_notify) {
        cv_.notify_one();
    }
}

void OtlpSpanExporter::flush_loop() {
    while (true) {
        std::vector<OtlpSpanRecord> batch;
        {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait_for(
                lock,
                std::chrono::milliseconds(flush_interval_ms_),
                [this] { return shutdown_ || static_cast<int>(pending_.size()) >= batch_size_; });
            batch.swap(pending_);
            if (shutdown_ && batch.empty()) {
                return;
            }
        }
        if (!batch.empty()) {
            do_flush(std::move(batch));
        }
    }
}

void OtlpSpanExporter::do_flush(std::vector<OtlpSpanRecord> batch) {
    const std::string body = build_otlp_json(service_name_, batch).dump();

    CURL* curl = curl_easy_init();
    if (!curl) return;

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL,           endpoint_.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS,    body.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, static_cast<long>(body.size()));
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER,    headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,       5L);

    curl_easy_perform(curl); // failures are silent -- tracing must never crash the app

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}
