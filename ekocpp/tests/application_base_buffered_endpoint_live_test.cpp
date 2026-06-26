// Live integration test, not a unit smoke test: a real ApplicationBase-
// derived app, with a real buffered endpoint, running a real TCP server,
// hit over the real wire by a real TransientTCPClient -- verifying the
// register_buffered_endpoint wiring end to end (push -> queue -> background
// loop -> processed, and a clean shutdown that drains the queue before the
// process actually exits), not just that each piece compiles in isolation.

#include <atomic>
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

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

std::atomic<int> g_processed_count{0};

bool buffered_echo_handler(SpanKey, RequestDTO&) {
    ++g_processed_count;
    return true;
}

class TestApp : public ApplicationBase {
public:
    TestApp() {
        register_buffered_endpoint("buffered_echo", buffered_echo_handler, /*page_size=*/100, /*max_retries=*/2);
    }
};

} // namespace

int main() {
    const std::string buffer_dir = "/tmp/ekocpp_buffered_endpoint_live_test";
    std::filesystem::remove_all(buffer_dir);
    std::filesystem::create_directories(buffer_dir);

    // ConfigTCP is deliberately instance-only (no app/global fallback tier --
    // see config_models.cpp's get_eco_env_optional("TCP", true) call), so the
    // bare ECOENV_TCP is silently ignored; it must be the fully-scoped name.
    setenv("ECOENV_TCP_APPLICATION_BASE_BUFFERED_ENDPOINT_LIVE_TEST_LIVE_TEST", "127.0.0.1:19999", 1);
    setenv("ECOENV_BUFFER_DIR", buffer_dir.c_str(), 1);

    char argv0[] = "application_base_buffered_endpoint_live_test";
    char arg1[] = "-i";
    char arg2[] = "live_test";
    char* argv[] = {argv0, arg1, arg2};
    const CommandLineArgs args = parse_command_line_args(3, argv);
    AppConfiguration::initialize(argv0, args);

    TestApp app;

    std::thread server_thread([&app]() { app.start(); });

    // Give the server a moment to actually bind+listen before the client tries to connect.
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    asio::io_context client_io_context(1);
    bool             request_completed = false;
    nlohmann::json   response_data;

    asio::co_spawn(client_io_context, [&]() -> asio::awaitable<void> {
        try {
            TransientTCPClient client(client_io_context.get_executor(), "127.0.0.1", 19999);
            const nlohmann::json request_data{{"hello", "world"}}; // named local, not inline -- see known_issues.md's GCC coroutine ICE
            response_data     = co_await client.send_message("buffered_echo", request_data);
            request_completed = true;
        } catch (const std::exception& e) {
            std::fprintf(stderr, "client exception: %s\n", e.what());
        }
    }, asio::detached);

    client_io_context.run();

    check(request_completed, "client received a response from the buffered endpoint over real TCP");
    check(response_data.contains("span_key"), "response envelope contains span_key (matches BufferedRequestHandler::push's shape)");

    // Give the background processing loop a moment to actually run and
    // process the item (it was spawned async by push(), not awaited by it).
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    check(g_processed_count.load() == 1, "buffered_echo_handler actually invoked once by the background processing loop");

    app.stop();
    server_thread.join(); // blocks until shut_down_buffered_handlers() has fully drained, then io_context_ stops, then start() returns

    // file_basename = {app_name}-{instance_id}-{route_key}-endpoint -- app_name
    // is derived from argv0's basename (see AppConfiguration::initialize).
    const std::string file_basename = "application_base_buffered_endpoint_live_test-live_test-buffered_echo-endpoint";
    check(std::filesystem::exists(buffer_dir + "/" + file_basename + "-pending.sqlite"), "pending queue SQLite file exists after shutdown");
    check(std::filesystem::exists(buffer_dir + "/" + file_basename + "-error.sqlite"), "error queue SQLite file exists after shutdown");

    std::printf("\nAll application_base_buffered_endpoint_live_test checks passed.\n");
    return 0;
}
