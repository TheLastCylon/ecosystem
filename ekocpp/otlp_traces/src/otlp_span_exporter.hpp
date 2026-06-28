#pragma once

#include <condition_variable>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "otlp_span_record.hpp"

// Buffers completed spans and ships them to an OTLP HTTP/JSON endpoint
// (e.g. Jaeger's /v1/traces). Mirrors the behaviour of OTel SDK's
// BatchSpanProcessor -- spans accumulate until batch_size is reached OR
// flush_interval_ms elapses, then a blocking HTTP POST fires on a dedicated
// background thread so the io_context is never stalled on a network call.
class OtlpSpanExporter {
public:
    OtlpSpanExporter(
        std::string endpoint,
        std::string service_name,
        int         batch_size        = 512,
        int         flush_interval_ms = 2000);

    ~OtlpSpanExporter(); // signals shutdown, joins flush thread

    void add_span(OtlpSpanRecord record); // thread-safe; called from the io_context thread

private:
    void flush_loop();
    void do_flush(std::vector<OtlpSpanRecord> batch);

    std::string endpoint_;
    std::string service_name_;
    int         batch_size_;
    int         flush_interval_ms_;

    std::mutex              mutex_;
    std::condition_variable cv_;
    std::vector<OtlpSpanRecord> pending_;
    bool        shutdown_ = false;
    std::thread flush_thread_;
};
