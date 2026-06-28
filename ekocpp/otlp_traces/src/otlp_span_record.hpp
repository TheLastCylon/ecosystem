#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

// A completed span -- all fields resolved, ready for serialisation and export.
struct OtlpSpanRecord {
    std::string  trace_id;       // 32 hex chars
    std::string  span_id;        // 16 hex chars
    std::string  parent_span_id; // 16 hex chars; empty string for root spans
    std::string  name;           // route_key for routing spans; "<route_key>.process" for buffered
    uint64_t     start_unix_nano = 0;
    uint64_t     end_unix_nano   = 0;
    bool         success         = true;
    std::vector<std::pair<std::string, std::string>> attributes;
};
