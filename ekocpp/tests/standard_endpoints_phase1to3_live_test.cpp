// Live test: eco.error_states.*, eco.statistics.get, eco.log.level/buffer --
// all auto-registered by ApplicationBase's own constructor, so a plain
// ApplicationBase-derived app with NO extra registrations already exposes
// them. Verifies the wiring end to end over real TCP.

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <thread>

#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/io_context.hpp>
#include <asio/use_awaitable.hpp>

#include "../src/application_base.hpp"
#include "../src/clients/transient_tcp_client.hpp"
#include "../src/configuration/argument_parser.hpp"
#include "../src/logs/eco_logger.hpp"
#include "../src/state_keepers/error_state_list.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

class TestApp : public ApplicationBase {};

} // namespace

int main() {
    setenv("ECOENV_TCP_STANDARD_ENDPOINTS_PHASE1TO3_LIVE_TEST_LIVE_TEST", "127.0.0.1:19998", 1);

    char argv0[] = "standard_endpoints_phase1to3_live_test";
    char arg1[] = "-i";
    char arg2[] = "live_test";
    char* argv[] = {argv0, arg1, arg2};
    const CommandLineArgs args = parse_command_line_args(3, argv);
    AppConfiguration::initialize(argv0, args);
    EcoLogger::instance().setup(); // eco.log.level dereferences EcoLogger's logger_ -- must be set up first, same as a real main()

    // Seed an error state directly (mirrors what a real handler would do --
    // ErrorStateList::instance().increment(...) on some failure path).
    ErrorStateList::instance().increment("DB_CONNECT", "Could not reach the database");
    ErrorStateList::instance().increment("DB_CONNECT", "Could not reach the database");
    ErrorStateList::instance().increment("DB_CONNECT", "Could not reach the database");

    TestApp app;
    std::thread server_thread([&app]() { app.start(); });
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    asio::io_context client_io_context(1);

    auto call = [&](const std::string& route_key, const nlohmann::json& data) -> nlohmann::json {
        nlohmann::json result;
        asio::co_spawn(client_io_context, [&]() -> asio::awaitable<void> {
            TransientTCPClient client(client_io_context.get_executor(), "127.0.0.1", 19998);
            const nlohmann::json request_copy = data; // named local -- avoid the GCC coroutine ICE (inline temporary in a co_await arg list)
            result = co_await client.send_message(route_key, request_copy);
        }, asio::detached);
        client_io_context.run();
        client_io_context.restart();
        return result;
    };

    {
        const auto response = call("eco.error_states.get", nlohmann::json::object());
        check(response.contains("errors"), "eco.error_states.get returns an errors array");
        check(response["errors"].size() == 1, "exactly one error_id is set (DB_CONNECT)");
        check(response["errors"][0]["error_id"] == "DB_CONNECT", "the reported error_id matches");
        check(response["errors"][0]["count"] == 3, "the error count matches the 3 increments");
    }

    {
        const auto response = call("eco.error_states.clear", nlohmann::json{{"error_id", "DB_CONNECT"}, {"count", 1}});
        check(response["errors"][0]["count"] == 2, "clear_some(1) reduced the count from 3 to 2");
    }

    {
        const auto response = call("eco.error_states.clear", nlohmann::json{{"error_id", "DB_CONNECT"}, {"count", 0}});
        check(response["errors"].empty(), "clear_all (count=0) removed DB_CONNECT from the reported errors");
    }

    {
        const auto response = call("eco.statistics.get", nlohmann::json{{"type", "current"}});
        check(response.contains("statistics"), "eco.statistics.get returns a statistics object");
        check(response["statistics"]["application"]["name"] == "standard_endpoints_phase1to3_live_test", "statistics.application.name reflects the real app name");
    }

    {
        const auto response = call("eco.log.level", nlohmann::json{{"level", "debug"}});
        check(response["level"] == "debug", "eco.log.level echoes back the level it set");
    }

    {
        const auto response = call("eco.log.buffer", nlohmann::json{{"size", 4096}});
        check(response["applied"] == false, "eco.log.buffer honestly reports applied=false (documented no-op)");
    }

    app.stop();
    server_thread.join();

    std::printf("\nAll standard_endpoints_phase1to3_live_test checks passed.\n");
    return 0;
}
