#include <cstdio>

#include "../src/state_keepers/statistics_keeper.hpp"
#include "../src/configuration/argument_parser.hpp"
#include "../src/configuration/config_models.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

} // namespace

int main(int argc, char** argv) {
    // StatisticsKeeper::update_current_statistics() reads AppConfiguration::instance() --
    // needs initialize() called first, same precondition ApplicationBase has.
    const CommandLineArgs args = parse_command_line_args(argc, argv);
    AppConfiguration::initialize(argv[0], args);

    auto& keeper = StatisticsKeeper::instance();

    // --- dotted-key increment/decrement/set, deep nesting via json_pointer ---
    keeper.increment("requests.total");
    keeper.increment("requests.total");
    keeper.increment("requests.total", 3);
    check(keeper.get_current_statistics()["requests"]["total"].get<double>() == 5.0, "increment accumulates across dotted-key calls");

    keeper.decrement("requests.total", 2);
    check(keeper.get_current_statistics()["requests"]["total"].get<double>() == 3.0, "decrement subtracts correctly");

    keeper.set_statistic_value("nested.deeply.value", 42.0);
    check(keeper.get_current_statistics()["nested"]["deeply"]["value"].get<double>() == 42.0, "set_statistic_value creates deep nesting");

    // --- endpoint duration tracking + percentile calc ---
    keeper.track_endpoint_data("echo");
    for (double d : {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}) {
        keeper.add_endpoint_stats("echo", d);
    }
    auto stats = keeper.get_current_statistics();
    check(stats["endpoint_data"]["echo"]["call_count"].get<double>() == 10.0, "add_endpoint_stats increments call_count");
    check(stats["endpoint_data"]["echo"]["p95"].get<double>() > 0.8, "p95 is in the upper range of recorded durations");
    check(stats["endpoint_data"]["echo"]["p99"].get<double>() >= stats["endpoint_data"]["echo"]["p95"].get<double>(), "p99 >= p95");

    // --- persisted queue size tracking via type-erased size getter ---
    size_t fake_queue_size = 7;
    keeper.add_persisted_queue("buffered_endpoint_sizes.echo.pending", [&fake_queue_size]() { return fake_queue_size; });
    check(keeper.get_current_statistics()["buffered_endpoint_sizes"]["echo"]["pending"].get<double>() == 7.0, "persisted queue size reflected via type-erased getter");
    fake_queue_size = 12;
    check(keeper.get_current_statistics()["buffered_endpoint_sizes"]["echo"]["pending"].get<double>() == 12.0, "persisted queue size getter re-invoked, not cached");

    // --- application name/instance populated from AppConfiguration ---
    check(!keeper.get_current_statistics()["application"]["name"].get<std::string>().empty(), "application.name populated from AppConfiguration");

    // --- gather_now: snapshots into history, then resets current counters ---
    check(keeper.get_full_gathered_statistics().empty(), "history starts empty");
    keeper.gather_now();
    check(keeper.get_full_gathered_statistics().size() == 1, "gather_now adds one history entry");
    check(keeper.get_last_gathered_statistics()["requests"]["total"].get<double>() == 3.0, "history snapshot captured the pre-reset value");
    check(keeper.get_current_statistics()["requests"]["total"].get<double>() == 0.0, "gather_now reset current counters to 0");

    // --- history trimming to history_length ---
    keeper.set_history_length(2);
    keeper.gather_now();
    keeper.gather_now();
    check(keeper.get_full_gathered_statistics().size() == 2, "history trimmed to history_length");

    std::printf("\nAll statistics_keeper smoke tests passed.\n");
    return 0;
}
