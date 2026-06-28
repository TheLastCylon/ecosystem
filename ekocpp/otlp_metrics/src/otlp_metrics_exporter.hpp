#pragma once

#include <condition_variable>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <vector>

#include "stats_translator.hpp"

// Accepts batches of MetricPoints from the scraper (called from the io_context
// coroutine) and ships them to an OTLP HTTP/JSON endpoint on a dedicated
// background thread -- same pattern as OtlpSpanExporter, same reason: curl's
// blocking HTTP POST must never stall the io_context.
//
// Each push() call enqueues one service's full scrape as a single
// resourceMetrics entry. The background thread dequeues and POSTs immediately
// (no batching delay -- metrics are already low-frequency, one push per
// gather period per service).
class OtlpMetricsExporter {
public:
    OtlpMetricsExporter(std::string endpoint, std::string scope_name);
    ~OtlpMetricsExporter();

    void push(
        const std::string&              service_name,
        const std::string&              instance,
        const std::vector<MetricPoint>& metrics,
        long long                       time_unix_nano
    );

private:
    struct Payload {
        std::string              service_name;
        std::string              instance;
        std::vector<MetricPoint> metrics;
        long long                time_unix_nano;
    };

    void send_loop();
    void do_send(const Payload& payload);

    std::string endpoint_;
    std::string scope_name_;

    std::mutex              mutex_;
    std::condition_variable cv_;
    std::queue<Payload>     queue_;
    bool                    shutdown_ = false;
    std::thread             send_thread_;
};
