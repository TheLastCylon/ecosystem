#include "statistics_keeper.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>

#include <spdlog/spdlog.h>

#include "../configuration/config_models.hpp"

namespace {

// --------------------------------------------------------------------------------
// "endpoint_data.echo.p95" -> "/endpoint_data/echo/p95" -- nlohmann::json's
// json_pointer does the deep get/set itself once converted, replacing
// Python's hand-rolled recursive __deep_get/__deep_set walk.
nlohmann::json::json_pointer to_pointer(const std::string& dotted_key) {
    std::string path = dotted_key;
    std::replace(path.begin(), path.end(), '.', '/');
    return nlohmann::json::json_pointer("/" + path);
}

// --------------------------------------------------------------------------------
double now_seconds() {
    return std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
}

} // namespace

// --------------------------------------------------------------------------------
StatisticsKeeper& StatisticsKeeper::instance() {
    static StatisticsKeeper keeper;
    return keeper;
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::increment(const std::string& key, double value) {
    const auto pointer  = to_pointer(key);
    const double current = statistics_current_.contains(pointer) ? statistics_current_.at(pointer).get<double>() : 0.0;
    statistics_current_[pointer] = current + value;
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::decrement(const std::string& key, double value) {
    increment(key, -value);
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::set_statistic_value(const std::string& key, double value) {
    statistics_current_[to_pointer(key)] = value;
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::add_persisted_queue(const std::string& key, std::function<size_t()> size_getter) {
    persisted_queues_[key] = std::move(size_getter);
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::track_endpoint_data(const std::string& key) {
    increment("endpoint_data." + key + ".call_count", 0.0);
    endpoint_durations_[key] = {};
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::add_endpoint_stats(const std::string& key, double duration_seconds) {
    increment("endpoint_data." + key + ".call_count");
    endpoint_durations_[key].push_back(duration_seconds);
}

// --------------------------------------------------------------------------------
// Nearest-rank percentile, not Python's statistics.quantiles(n=100) exclusive
// method -- this is a deliberate, known divergence (see statistics_keeper.hpp),
// not an attempt at bit-for-bit parity. Fine for an internal dashboard stat.
StatisticsKeeper::EndpointPercentiles StatisticsKeeper::percentiles_for(std::vector<double> durations) {
    if (durations.empty()) return {-1.0, -1.0};
    if (durations.size() == 1) return {durations[0], durations[0]};

    std::sort(durations.begin(), durations.end());
    auto rank = [&durations](double percentile) {
        const size_t index = static_cast<size_t>(std::ceil(percentile / 100.0 * static_cast<double>(durations.size()))) - 1;
        return durations[std::min(index, durations.size() - 1)];
    };
    return {rank(95.0), rank(99.0)};
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::update_current_statistics() {
    const double current_time = now_seconds();

    statistics_current_["timestamp"]               = current_time;
    statistics_current_["uptime"]                  = current_time - start_time_;
    statistics_current_["gather_period"]           = gather_period_;
    statistics_current_["application"]["name"]     = AppConfiguration::instance().name();
    statistics_current_["application"]["instance"] = AppConfiguration::instance().instance_id();

    for (const auto& [key, durations] : endpoint_durations_) {
        const EndpointPercentiles percentiles = percentiles_for(durations);
        set_statistic_value("endpoint_data." + key + ".p95", percentiles.p95);
        set_statistic_value("endpoint_data." + key + ".p99", percentiles.p99);
    }

    for (const auto& [key, size_getter] : persisted_queues_) {
        set_statistic_value(key, static_cast<double>(size_getter()));
    }
}

// --------------------------------------------------------------------------------
nlohmann::json StatisticsKeeper::get_current_statistics() {
    update_current_statistics();
    return statistics_current_;
}

// --------------------------------------------------------------------------------
const nlohmann::json& StatisticsKeeper::get_last_gathered_statistics() const {
    static const nlohmann::json empty = nlohmann::json::object();
    return statistics_history_.empty() ? empty : statistics_history_.front();
}

// --------------------------------------------------------------------------------
const std::vector<nlohmann::json>& StatisticsKeeper::get_full_gathered_statistics() const {
    return statistics_history_;
}

// --------------------------------------------------------------------------------
// Zeroes every leaf value regardless of type -- matches Python's
// __reset_stats exactly, including the quirk that it also zeroes
// non-numeric leaves like application.name/instance until the next
// update_current_statistics() call repopulates them. Harmless in practice:
// nothing reads statistics_current_ between a reset and the next update.
void StatisticsKeeper::reset_stats(nlohmann::json& node) {
    for (auto& [key, value] : node.items()) {
        if (value.is_object()) {
            reset_stats(value);
        } else {
            value = 0;
        }
    }
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::gather_now() {
    spdlog::info("Gathering statistics");
    update_current_statistics();

    statistics_history_.insert(statistics_history_.begin(), statistics_current_);
    if (statistics_history_.size() > history_length_) {
        statistics_history_.pop_back();
    }

    for (auto& [key, durations] : endpoint_durations_) {
        durations.clear();
    }
    reset_stats(statistics_current_);
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::start() {
    start_time_ = now_seconds();
    running_    = true;
    spdlog::info("Starting stats gathering.");
}

// --------------------------------------------------------------------------------
void StatisticsKeeper::stop() {
    running_ = false;
    spdlog::info("Stopping stats gathering.");
}
