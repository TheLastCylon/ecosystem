#include "otlp_metrics_exporter.hpp"

#include <string>
#include <utility>

#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

namespace {

static const std::unordered_map<std::string, std::string> METRIC_DESCRIPTIONS{
    {"ekosis_service_health",                  "1 if service responded to last stats poll, 0 otherwise"},
    {"ekosis_uptime_seconds",                  "Seconds the service has been running since startup"},
    {"ekosis_gather_period_seconds",           "Statistics gather period in seconds"},
    {"ekosis_endpoint_call_count",             "Total endpoint calls in the last gather period"},
    {"ekosis_endpoint_p95_seconds",            "95th percentile response time in seconds"},
    {"ekosis_endpoint_p99_seconds",            "99th percentile response time in seconds"},
    {"ekosis_buffered_endpoint_queue_pending", "Items pending in the buffered endpoint incoming queue"},
    {"ekosis_buffered_endpoint_queue_error",   "Items in the buffered endpoint error queue"},
    {"ekosis_buffered_sender_queue_pending",   "Items pending in the buffered sender outgoing queue"},
    {"ekosis_buffered_sender_queue_error",     "Items in the buffered sender error queue"},
};

nlohmann::json make_string_attr(const std::string& key, const std::string& value) {
    return {{"key", key}, {"value", {{"stringValue", value}}}};
}

nlohmann::json build_otlp_json(
    const std::string&              service_name,
    const std::string&              instance,
    const std::vector<MetricPoint>& metrics,
    long long                       time_unix_nano,
    const std::string&              scope_name)
{
    const std::string time_ns_str = std::to_string(time_unix_nano);

    // Build one metric object per unique metric name.
    // Each MetricPoint becomes one dataPoint under its gauge.
    std::vector<nlohmann::json> metric_objects;
    metric_objects.reserve(metrics.size());

    for (const MetricPoint& mp : metrics) {
        nlohmann::json dp_attrs = nlohmann::json::array();
        for (const auto& [k, v] : mp.labels) {
            dp_attrs.push_back(make_string_attr(k, v));
        }

        nlohmann::json data_point = {
            {"attributes",    std::move(dp_attrs)},
            {"timeUnixNano",  time_ns_str},
            {"asDouble",      mp.value},
        };

        const std::string desc = [&]() -> std::string {
            auto it = METRIC_DESCRIPTIONS.find(mp.name);
            return it != METRIC_DESCRIPTIONS.end() ? it->second : mp.name;
        }();

        metric_objects.push_back({
            {"name",        mp.name},
            {"description", desc},
            {"gauge",       {{"dataPoints", nlohmann::json::array({std::move(data_point)})}}}
        });
    }

    return nlohmann::json{
        {"resourceMetrics", {{
            {"resource", {{"attributes", {
                make_string_attr("service.name",        service_name),
                make_string_attr("service.instance.id", instance),
            }}}},
            {"scopeMetrics", {{
                {"scope",   {{"name", scope_name}}},
                {"metrics", std::move(metric_objects)},
            }}}
        }}}
    };
}

} // namespace

OtlpMetricsExporter::OtlpMetricsExporter(std::string endpoint, std::string scope_name)
    : endpoint_(std::move(endpoint))
    , scope_name_(std::move(scope_name))
    , send_thread_([this] { send_loop(); })
{}

OtlpMetricsExporter::~OtlpMetricsExporter() {
    {
        std::unique_lock<std::mutex> lock(mutex_);
        shutdown_ = true;
    }
    cv_.notify_one();
    send_thread_.join();
}

void OtlpMetricsExporter::push(
    const std::string&              service_name,
    const std::string&              instance,
    const std::vector<MetricPoint>& metrics,
    long long                       time_unix_nano)
{
    if (metrics.empty()) return;
    {
        std::unique_lock<std::mutex> lock(mutex_);
        queue_.push({service_name, instance, metrics, time_unix_nano});
    }
    cv_.notify_one();
}

void OtlpMetricsExporter::send_loop() {
    while (true) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_.wait(lock, [this] { return shutdown_ || !queue_.empty(); });

        if (shutdown_ && queue_.empty()) return;

        Payload payload = std::move(queue_.front());
        queue_.pop();
        lock.unlock();

        do_send(payload);
    }
}

void OtlpMetricsExporter::do_send(const Payload& payload) {
    const std::string body = build_otlp_json(
        payload.service_name, payload.instance,
        payload.metrics, payload.time_unix_nano,
        scope_name_
    ).dump();

    CURL* curl = curl_easy_init();
    if (!curl) return;

    std::string response_body;
    auto write_cb = +[](char* ptr, size_t size, size_t nmemb, void* userdata) -> size_t {
        static_cast<std::string*>(userdata)->append(ptr, size * nmemb);
        return size * nmemb;
    };

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL,            endpoint_.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS,     body.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE,  static_cast<long>(body.size()));
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER,     headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,        5L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION,  write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA,      &response_body);

    const CURLcode res = curl_easy_perform(curl);

    if (res != CURLE_OK) {
        spdlog::warn("OtlpMetricsExporter: curl error: {}", curl_easy_strerror(res));
    } else {
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
        if (http_code < 200 || http_code >= 300) {
            spdlog::warn("OtlpMetricsExporter: HTTP {}: {}", http_code, response_body);
        } else {
            spdlog::debug("OtlpMetricsExporter: HTTP {}: {}", http_code, response_body);
        }
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}
