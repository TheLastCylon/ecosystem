#include <cstdio>
#include <filesystem>
#include <functional>
#include <memory>

#include <asio/io_context.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/use_awaitable.hpp>

#include "../src/sending/buffered_sender.hpp"
#include "../src/data_transfer_objects/binary_frame.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

// Overrides only the one virtual seam ClientBase exposes -- send_message's
// own status-code interpretation (-> ServerBusyException etc.) and frame
// parsing run for real; only the "go over the network" part is faked.
class FakeClient : public ClientBase {
public:
    std::function<asio::awaitable<std::vector<uint8_t>>(std::vector<uint8_t>)> behavior;
    int call_count = 0;

protected:
    asio::awaitable<std::vector<uint8_t>> send_message_retry_loop(std::vector<uint8_t> request) override {
        ++call_count;
        co_return co_await behavior(std::move(request));
    }
};

asio::awaitable<std::vector<uint8_t>> status_response(const std::vector<uint8_t>& request, int status) {
    const ParsedHeader   parsed = parse_header(request.data());
    const nlohmann::json response_json{{"status", status}, {"data", nlohmann::json::object()}};
    co_return pack_frame(parsed.span_key, "", nlohmann::json::to_msgpack(response_json));
}

} // namespace

int main() {
    const std::string dir = "/tmp/ekocpp_buffered_sender_smoke_test";
    std::filesystem::remove_all(dir);
    std::filesystem::create_directories(dir);

    asio::io_context io_context(1);

    // --- Basic success path ---
    {
        auto client = std::make_shared<FakeClient>();
        client->behavior = [](std::vector<uint8_t> request) -> asio::awaitable<std::vector<uint8_t>> {
            co_return co_await status_response(request, static_cast<int>(Status::SUCCESS));
        };

        auto sender = std::make_shared<BufferedSender>(
            io_context.get_executor(), client, "outbound_echo", dir, "basic-sender", std::chrono::milliseconds{0}, 100, 3
        );
        sender->unpause_send_process();

        sender->enqueue(nlohmann::json{{"x", 1}});
        io_context.run();

        check(client->call_count == 1, "client called exactly once for a successful send");
        check(sender->pending_queue_size() == 0, "pending queue drained after a successful send");
        check(sender->error_queue_size() == 0, "no error-queue entry on success");

        io_context.restart();
    }

    // --- ServerBusyException retried, then succeeds ---
    {
        auto client = std::make_shared<FakeClient>();
        client->behavior = [](std::vector<uint8_t> request) -> asio::awaitable<std::vector<uint8_t>> {
            static int attempt = 0;
            ++attempt;
            co_return co_await status_response(request, attempt < 3 ? static_cast<int>(Status::APPLICATION_BUSY) : static_cast<int>(Status::SUCCESS));
        };

        auto sender = std::make_shared<BufferedSender>(
            io_context.get_executor(), client, "outbound_retry", dir, "retry-sender", std::chrono::milliseconds{0}, 100, 5
        );
        sender->unpause_send_process();

        sender->enqueue(nlohmann::json{{"x", 1}});
        io_context.run();

        check(client->call_count == 3, "ServerBusyException retried until success on the 3rd attempt");
        check(sender->pending_queue_size() == 0, "pending queue drained after eventual success");
        check(sender->error_queue_size() == 0, "no error-queue entry for an eventually-successful send");

        io_context.restart();
    }

    // --- Max retries exceeded on a retryable failure -> error queue, not infinite retry ---
    {
        auto client = std::make_shared<FakeClient>();
        client->behavior = [](std::vector<uint8_t> request) -> asio::awaitable<std::vector<uint8_t>> {
            co_return co_await status_response(request, static_cast<int>(Status::APPLICATION_BUSY));
        };

        auto sender = std::make_shared<BufferedSender>(
            io_context.get_executor(), client, "outbound_always_busy", dir, "busy-sender", std::chrono::milliseconds{0}, 100, 2
        );
        sender->unpause_send_process();

        sender->enqueue(nlohmann::json{{"x", 1}});
        io_context.run();

        check(sender->pending_queue_size() == 0, "pending queue empty after exhausting retries on a busy server");
        check(sender->error_queue_size() == 1, "permanently-busy send routed to error queue after max_retries");

        io_context.restart();
    }

    // --- A non-retryable exception (not ServerBusy/CommunicationsMaxRetriesReached) routes straight to error, no retry ---
    {
        auto client = std::make_shared<FakeClient>();
        client->behavior = [](std::vector<uint8_t>) -> asio::awaitable<std::vector<uint8_t>> {
            throw std::runtime_error("simulated unrelated failure");
            co_return std::vector<uint8_t>{}; // unreachable, satisfies the coroutine's return type
        };

        auto sender = std::make_shared<BufferedSender>(
            io_context.get_executor(), client, "outbound_broken", dir, "broken-sender", std::chrono::milliseconds{0}, 100, 5
        );
        sender->unpause_send_process();

        sender->enqueue(nlohmann::json{{"x", 1}});
        io_context.run();

        check(client->call_count == 1, "non-retryable exception is NOT retried -- exactly one attempt");
        check(sender->pending_queue_size() == 0, "pending queue empty -- item didn't get retried");
        check(sender->error_queue_size() == 1, "non-retryable exception routed straight to error queue");

        io_context.restart();
    }

    // --- Shutdown: drains gracefully, queue.shut_down() deferred until the loop actually exits ---
    {
        auto client = std::make_shared<FakeClient>();
        client->behavior = [](std::vector<uint8_t> request) -> asio::awaitable<std::vector<uint8_t>> {
            co_return co_await status_response(request, static_cast<int>(Status::SUCCESS));
        };

        auto sender = std::make_shared<BufferedSender>(
            io_context.get_executor(), client, "outbound_shutdown", dir, "shutdown-sender"
        );
        sender->unpause_send_process();
        sender->enqueue(nlohmann::json{{"x", 1}});

        bool shutdown_completed = false;
        asio::co_spawn(io_context, [sender, &shutdown_completed]() -> asio::awaitable<void> {
            co_await sender->shut_down();
            shutdown_completed = true;
        }, asio::detached);

        io_context.run();
        check(shutdown_completed, "shut_down() coroutine completed");
        check(sender->is_send_process_paused(), "shut_down pauses the send process");

        io_context.restart();
    }

    std::printf("\nAll buffered_sender smoke tests passed.\n");
    return 0;
}
