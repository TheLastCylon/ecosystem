#include "stats_translator.hpp"

#include <algorithm>
#include <string>

namespace {

std::string safe_key(const std::string& key) {
    std::string result = key;
    std::replace(result.begin(), result.end(), '.', '_');
    std::replace(result.begin(), result.end(), '-', '_');
    return result;
}

// Recursively flattens a JSON object into (dotted_name, double) pairs.
void flatten(
    const nlohmann::json&    obj,
    const std::string&       prefix,
    std::vector<std::pair<std::string, double>>& out)
{
    if (obj.is_object()) {
        for (const auto& [key, val] : obj.items()) {
            const std::string next = prefix.empty() ? safe_key(key) : prefix + "_" + safe_key(key);
            flatten(val, next, out);
        }
    } else if (obj.is_number()) {
        out.emplace_back(prefix, obj.get<double>());
    }
}

void iter_queue_groups(
    const nlohmann::json&                  queue_data,
    const std::unordered_set<std::string>& exclude_groups,
    const std::string&                     metric_prefix,
    const std::map<std::string, std::string>& base_labels,
    std::vector<MetricPoint>&              out)
{
    if (!queue_data.is_object()) return;
    for (const auto& [group, endpoints] : queue_data.items()) {
        if (exclude_groups.count(group)) continue;
        if (!endpoints.is_object()) continue;
        for (const auto& [endpoint_name, sizes] : endpoints.items()) {
            if (!sizes.is_object()) continue;
            auto labels = base_labels;
            labels["group"]    = group;
            labels["endpoint"] = endpoint_name;

            if (sizes.contains("pending") && sizes["pending"].is_number()) {
                out.push_back({metric_prefix + "_queue_pending", sizes["pending"].get<double>(), labels});
            }
            if (sizes.contains("error") && sizes["error"].is_number()) {
                out.push_back({metric_prefix + "_queue_error", sizes["error"].get<double>(), labels});
            }
        }
    }
}

} // namespace

std::vector<MetricPoint> translate_gathered_stats(
    const nlohmann::json&                  stats,
    const std::string&                     fallback_name,
    const std::string&                     fallback_instance,
    const std::unordered_set<std::string>& exclude_groups)
{
    std::vector<MetricPoint> out;

    const auto& app      = stats.contains("application") ? stats["application"] : nlohmann::json::object();
    const std::string svc_name = app.value("name",     fallback_name);
    const std::string instance = app.value("instance", fallback_instance);

    const std::map<std::string, std::string> base_labels{{"service", svc_name}, {"instance", instance}};

    if (stats.contains("uptime") && stats["uptime"].is_number()) {
        out.push_back({"ekosis_uptime_seconds", stats["uptime"].get<double>(), base_labels});
    }

    if (stats.contains("gather_period") && stats["gather_period"].is_number()) {
        out.push_back({"ekosis_gather_period_seconds", stats["gather_period"].get<double>(), base_labels});
    }

    if (stats.contains("endpoint_data") && stats["endpoint_data"].is_object()) {
        for (const auto& [group, endpoints] : stats["endpoint_data"].items()) {
            if (exclude_groups.count(group)) continue;
            if (!endpoints.is_object()) continue;
            for (const auto& [endpoint_name, data] : endpoints.items()) {
                if (!data.is_object()) continue;
                auto labels = base_labels;
                labels["group"]    = group;
                labels["endpoint"] = endpoint_name;

                if (data.contains("call_count") && data["call_count"].is_number()) {
                    out.push_back({"ekosis_endpoint_call_count", data["call_count"].get<double>(), labels});
                }
                if (data.contains("p95") && data["p95"].is_number() && data["p95"].get<double>() >= 0) {
                    out.push_back({"ekosis_endpoint_p95_seconds", data["p95"].get<double>(), labels});
                }
                if (data.contains("p99") && data["p99"].is_number() && data["p99"].get<double>() >= 0) {
                    out.push_back({"ekosis_endpoint_p99_seconds", data["p99"].get<double>(), labels});
                }
            }
        }
    }

    iter_queue_groups(
        stats.value("buffered_endpoint_sizes", nlohmann::json::object()),
        exclude_groups, "ekosis_buffered_endpoint", base_labels, out);

    iter_queue_groups(
        stats.value("buffered_sender_sizes", nlohmann::json::object()),
        exclude_groups, "ekosis_buffered_sender", base_labels, out);

    // Custom stats -- any top-level key not in the known set
    static const std::unordered_set<std::string> known_keys{
        "application", "endpoint_data", "buffered_endpoint_sizes",
        "buffered_sender_sizes", "timestamp", "uptime", "gather_period",
    };
    for (const auto& [key, val] : stats.items()) {
        if (known_keys.count(key)) continue;
        std::vector<std::pair<std::string, double>> flat;
        flatten(val, key, flat);
        for (auto& [suffix, metric_val] : flat) {
            out.push_back({"ekosis_custom_" + suffix, metric_val, base_labels});
        }
    }

    return out;
}
