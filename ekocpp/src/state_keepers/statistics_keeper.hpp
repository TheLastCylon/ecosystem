#pragma once

#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

#include <nlohmann/json.hpp>

// Mirrors ekosis/state_keepers/statistics_keeper.py's StatisticsKeeper.
//
// Plain Meyers singleton (static local in instance()) -- unlike
// AppConfiguration, this needs zero construction arguments, so there's no
// two-phase initialize()/instance() split to justify; see application_base.hpp's
// comment for why AppConfiguration deliberately ISN'T this simpler shape.
//
// Purely a synchronous data class -- no asio/io_context dependency. Python's
// gather_statistics() periodic loop (sleep gather_period seconds, snapshot,
// reset) is deliberately NOT ported here yet: nothing in ekocpp owns an
// io_context to co_spawn it onto, and no eco.statistics.get endpoint exists
// to read the result -- same "defer until a real consumer exists" rule
// already applied to ApplicationBase's buffered-handler/statistics-keeper
// scoping. gather_now() (the synchronous snapshot+reset half of that loop)
// is exposed directly so a future timer coroutine can just call it.
//
// add_persisted_queue takes a size getter, not a PaginatedQueue<T> itself --
// Python's runtime-erased generics let it store any PaginatedQueue directly;
// C++ has a different concrete type per QueuedType, and StatisticsKeeper
// only ever calls .size() on it, so erasing down to std::function<size_t()>
// is the direct equivalent of how HandlerWrapper erases handler signatures.
class StatisticsKeeper {
public:
    static StatisticsKeeper& instance();

    void set_gather_period(int seconds) { gather_period_ = seconds; }
    void set_history_length(size_t length) { history_length_ = length; }
    int gather_period() const { return gather_period_; }

    void increment(const std::string& key, double value = 1.0);
    void decrement(const std::string& key, double value = 1.0);
    void set_statistic_value(const std::string& key, double value);

    void add_persisted_queue(const std::string& key, std::function<size_t()> size_getter);

    // track_endpoint_data initializes the call_count + duration list for a
    // key (so it shows up in stats even before the first call completes);
    // add_endpoint_stats records one completed call's duration.
    void track_endpoint_data(const std::string& key);
    void add_endpoint_stats(const std::string& key, double duration_seconds = 0.0);

    // Recomputes timestamp/uptime/application/percentiles/persisted-queue
    // sizes into the current snapshot, then returns it.
    nlohmann::json get_current_statistics();
    const nlohmann::json& get_last_gathered_statistics() const;
    const std::vector<nlohmann::json>& get_full_gathered_statistics() const;

    // The synchronous half of Python's gather_statistics() periodic loop --
    // snapshot current statistics into history (trimmed to history_length_),
    // then reset counters/durations for the next period. Called manually
    // for now (tests, or an ad-hoc admin trigger); a timer coroutine calling
    // this on a schedule is future ApplicationBase wiring, not built yet.
    void gather_now();

    void start();
    void stop();
    bool is_running() const { return running_; }

private:
    StatisticsKeeper() = default;

    struct EndpointPercentiles {
        double p95;
        double p99;
    };

    static EndpointPercentiles percentiles_for(std::vector<double> durations);
    void update_current_statistics();
    static void reset_stats(nlohmann::json& node);

    bool   running_        = false;
    int    gather_period_  = 300;
    size_t history_length_ = 12;
    double start_time_     = 0.0;

    nlohmann::json               statistics_current_ = nlohmann::json::object();
    std::vector<nlohmann::json>  statistics_history_;

    std::unordered_map<std::string, std::function<size_t()>> persisted_queues_;
    std::unordered_map<std::string, std::vector<double>>     endpoint_durations_;
};
