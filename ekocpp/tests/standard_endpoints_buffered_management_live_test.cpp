// Live test: eco.buffered_handler.* and eco.buffered_sender.* admin
// endpoints, registered automatically by ApplicationBase's constructor,
// exercised against real handlers/senders registered by a derived app --
// over real TCP, not just unit-level calls into the registry.

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
#include "../src/data_transfer_objects/binary_frame.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

bool always_fails_handler(SpanKey, RequestDTO&) { return false; }

// Same fake transport-seam override as buffered_sender_smoke_test -- only
// the "go over the network" part is faked, send_message's real status
// interpretation still runs.
class AlwaysFailClient : public ClientBase {
protected:
    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t>) override {
        throw std::runtime_error("simulated send failure");
        co_return std::vector<uint8_t>{};
    }
};

class TestApp : public ApplicationBase {
public:
    std::shared_ptr<BufferedSender> sender;

    TestApp(int argc, char** argv) : ApplicationBase(argc, argv) {
        register_buffered_endpoint("managed_handler", always_fails_handler, /*page_size=*/100, /*max_retries=*/0);
        sender = register_buffered_sender("managed_sender", std::make_shared<AlwaysFailClient>(), std::chrono::milliseconds{0}, 100, 0);
    }
};

} // namespace

int main() {
    const std::string buffer_dir = "/tmp/ekocpp_buffered_management_live_test";
    std::filesystem::remove_all(buffer_dir);
    std::filesystem::create_directories(buffer_dir);

    setenv("ECOENV_TCP_STANDARD_ENDPOINTS_BUFFERED_MANAGEMENT_LIVE_TEST_LIVE_TEST", "127.0.0.1:19997", 1);
    setenv("ECOENV_BUFFER_DIR", buffer_dir.c_str(), 1);

    char argv0[] = "standard_endpoints_buffered_management_live_test";
    char arg1[] = "-i";
    char arg2[] = "live_test";
    char* argv[] = {argv0, arg1, arg2};

    TestApp app(3, argv);
    std::thread server_thread([&app]() { app.start(); });
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    asio::io_context client_io_context(1);

    auto call = [&](const std::string& route_key, const nlohmann::json& data) -> nlohmann::json {
        nlohmann::json result;
        asio::co_spawn(client_io_context, [&]() -> asio::awaitable<void> {
            TransientTCPClient   client(client_io_context.get_executor(), "127.0.0.1", 19997);
            const nlohmann::json request_copy = data;
            result = co_await client.send_message(route_key, request_copy);
        }, asio::detached);
        client_io_context.run();
        client_io_context.restart();
        return result;
    };

    // === Handler management ===

    // Push one item -- always_fails_handler with max_retries=0 routes it
    // straight to the error queue on the very first attempt.
    call("managed_handler", nlohmann::json{{"x", 1}});
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    {
        const auto response = call("eco.buffered_handler.data", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["database_sizes"]["error"] == 1, "one item landed in the handler's error queue");
        check(response["queue_data"]["receiving_paused"] == false, "receiving is unpaused by default after registration");
    }

    std::string error_span_key;
    {
        const auto response = call("eco.buffered_handler.errors.get_first_10", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"].size() == 1, "get_first_10 returns exactly the one error entry");
        error_span_key = response["queue_data"][0].get<std::string>();
    }

    {
        const auto response = call("eco.buffered_handler.errors.inspect_request", nlohmann::json{{"queue_route_key", "managed_handler"}, {"span_key", error_span_key}});
        check(response["request_data"]["x"] == 1, "inspect_request returns the original payload without removing it");
    }
    {
        const auto response = call("eco.buffered_handler.data", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["database_sizes"]["error"] == 1, "inspect_request did not consume the entry");
    }

    {
        const auto response = call("eco.buffered_handler.errors.pop_request", nlohmann::json{{"queue_route_key", "managed_handler"}, {"span_key", error_span_key}});
        check(response["request_data"]["x"] == 1, "pop_request returns the payload");
    }
    {
        const auto response = call("eco.buffered_handler.data", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["database_sizes"]["error"] == 0, "pop_request actually removed the entry");
    }

    {
        const auto response = call("eco.buffered_handler.receiving.pause", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["receiving_paused"] == true, "receiving.pause sets the flag");
    }
    {
        bool threw_busy = false;
        asio::co_spawn(client_io_context, [&]() -> asio::awaitable<void> {
            try {
                TransientTCPClient client(client_io_context.get_executor(), "127.0.0.1", 19997);
                const nlohmann::json data{{"x", 2}};
                co_await client.send_message("managed_handler", data);
            } catch (const ServerBusyException&) {
                threw_busy = true;
            }
        }, asio::detached);
        client_io_context.run();
        client_io_context.restart();
        check(threw_busy, "pushing to a receiving-paused handler throws ServerBusyException over the real wire");
    }
    {
        const auto response = call("eco.buffered_handler.receiving.unpause", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["receiving_paused"] == false, "receiving.unpause clears the flag");
    }

    {
        const auto response = call("eco.buffered_handler.all.pause", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["receiving_paused"] == true && response["queue_data"]["processing_paused"] == true, "all.pause sets both flags");
    }
    {
        const auto response = call("eco.buffered_handler.all.unpause", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["receiving_paused"] == false && response["queue_data"]["processing_paused"] == false, "all.unpause clears both flags");
    }

    // Push another failing item, then exercise reprocess.all / clear.
    call("managed_handler", nlohmann::json{{"x", 3}});
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    {
        const auto response = call("eco.buffered_handler.errors.reprocess.all", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["message"].get<std::string>().find("moved to incoming database") != std::string::npos, "reprocess.all reports the move");
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    {
        // It always fails again, so it should be straight back in the error queue.
        const auto response = call("eco.buffered_handler.data", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["database_sizes"]["error"] == 1, "reprocessed item failed again and landed back in error queue");
    }
    {
        const auto response = call("eco.buffered_handler.errors.clear", nlohmann::json{{"queue_route_key", "managed_handler"}});
        check(response["queue_data"]["database_sizes"]["error"] == 0, "errors.clear empties the error queue");
    }

    {
        const auto response = call("eco.buffered_handler.data", nlohmann::json{{"queue_route_key", "no_such_route"}});
        check(response["queue_data"].is_null(), "unknown route_key returns null queue_data");
        check(response["message"].get<std::string>().find("No queue for route key") != std::string::npos, "unknown route_key gets the right message");
    }

    // === Sender management ===

    app.sender->enqueue(nlohmann::json{{"y", 1}});
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    {
        const auto response = call("eco.buffered_sender.data", nlohmann::json{{"queue_route_key", "managed_sender"}});
        check(response["queue_data"]["database_sizes"]["error"] == 1, "sender's always-failing client routed the item to the error queue");
    }

    std::string sender_error_span_key;
    {
        const auto response = call("eco.buffered_sender.errors.get_first_10", nlohmann::json{{"queue_route_key", "managed_sender"}});
        check(response["queue_data"].size() == 1, "sender errors.get_first_10 returns the one entry");
        sender_error_span_key = response["queue_data"][0].get<std::string>();
    }

    {
        const auto response = call("eco.buffered_sender.errors.inspect_request", nlohmann::json{{"queue_route_key", "managed_sender"}, {"span_key", sender_error_span_key}});
        check(response["request_data"]["y"] == 1, "sender inspect_request returns the payload");
    }

    {
        const auto response = call("eco.buffered_sender.send_process.pause", nlohmann::json{{"queue_route_key", "managed_sender"}});
        check(response["queue_data"]["send_process_paused"] == true, "send_process.pause sets the flag");
    }
    {
        const auto response = call("eco.buffered_sender.send_process.unpause", nlohmann::json{{"queue_route_key", "managed_sender"}});
        check(response["queue_data"]["send_process_paused"] == false, "send_process.unpause clears the flag");
    }

    {
        const auto response = call("eco.buffered_sender.errors.pop_request", nlohmann::json{{"queue_route_key", "managed_sender"}, {"span_key", sender_error_span_key}});
        check(response["request_data"]["y"] == 1, "sender pop_request returns the payload and removes it");
    }
    {
        const auto response = call("eco.buffered_sender.data", nlohmann::json{{"queue_route_key", "managed_sender"}});
        check(response["queue_data"]["database_sizes"]["error"] == 0, "sender error queue empty after pop_request");
    }

    {
        const auto response = call("eco.buffered_sender.data", nlohmann::json{{"queue_route_key", "no_such_sender"}});
        check(response["queue_data"].is_null(), "unknown sender route_key returns null queue_data");
    }

    app.stop();
    server_thread.join();

    std::printf("\nAll standard_endpoints_buffered_management_live_test checks passed.\n");
    return 0;
}
