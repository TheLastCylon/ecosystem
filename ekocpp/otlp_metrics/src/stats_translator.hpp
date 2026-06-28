#pragma once

#include <map>
#include <string>
#include <unordered_set>
#include <vector>

#include <nlohmann/json.hpp>

struct MetricPoint {
    std::string                        name;
    double                             value;
    std::map<std::string, std::string> labels;
};

// Mirrors ekosis_prometheus/stats_translator.py's translate_gathered_stats().
// Yields MetricPoints from a gathered eco.statistics.get response.
// exclude_groups defaults to {"eco"} -- filters out EcoSystem internal endpoints.
std::vector<MetricPoint> translate_gathered_stats(
    const nlohmann::json&                  stats,
    const std::string&                     service_name,
    const std::string&                     instance,
    const std::unordered_set<std::string>& exclude_groups = {"eco"}
);
