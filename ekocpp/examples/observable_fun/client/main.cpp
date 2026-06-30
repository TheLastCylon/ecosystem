#include <atomic>
#include <chrono>
#include <cstdlib>
#include <memory>
#include <string>
#include <vector>

#include <asio/awaitable.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/steady_timer.hpp>
#include <asio/use_awaitable.hpp>
#include <spdlog/spdlog.h>

#include "application_base.hpp"
#include "clients/udp_client.hpp"
#include "data_transfer_objects/span_key.hpp"

#include "router_dto.hpp"

// C++ equivalent of observable_fun/router/client.py.
// Each worker coroutine has its own UDPClient (its own socket and send_permit_)
// so sends are truly concurrent across workers -- no permit contention.
// Usage: client [workers]   default workers = 8

namespace {

const std::vector<std::string> MESSAGES = {"fortune", "joke", "lotto 3", "time", "question"};

std::string pick_message() {
    return MESSAGES[static_cast<size_t>(std::rand()) % MESSAGES.size()];  // NOLINT
}

} // namespace

class LoadClient : public ApplicationBase {
public:
    LoadClient(int argc, char** argv) : ApplicationBase(argc, argv) {
        if (argc > 1) {
            try { worker_count_ = std::stoi(argv[1]); } catch (...) {}
        }
    }

protected:
    void setup_tasks() override {
        spdlog::info("Starting {} worker(s)", worker_count_);
        auto exec = io_context().get_executor();
        for (int i = 0; i < worker_count_; ++i) {
            auto client = std::make_shared<UDPClient>(exec, "127.0.0.1", 8600);
            clients_.push_back(client);
            asio::co_spawn(io_context(), worker(client), asio::detached);
        }
        asio::co_spawn(io_context(), stats_reporter(), asio::detached);
    }

private:
    asio::awaitable<void> worker(std::shared_ptr<UDPClient> client) {
        while (true) {
            try {
                auto span_key = SpanKey::generate();
                auto response = co_await client->send_message<RouterRequestDto, RouterResponseDto>(
                    "app.process_message",
                    RouterRequestDto{pick_message()},
                    span_key
                );
                spdlog::info("RCV: [{}], {}", span_key.to_string(), response.response);
                ++request_count_;
            } catch (...) {}
        }
    }

    asio::awaitable<void> stats_reporter() {
        asio::steady_timer timer(co_await asio::this_coro::executor);
        uint64_t last = 0;
        while (true) {
            timer.expires_after(std::chrono::seconds{1});
            co_await timer.async_wait(asio::use_awaitable);
            const uint64_t current = request_count_.load();
            spdlog::info("req/s: {}", current - last);
            last = current;
        }
    }

    int                                     worker_count_  = 1;
    std::atomic<uint64_t>                   request_count_ = 0;
    std::vector<std::shared_ptr<UDPClient>> clients_;
};

int main(int argc, char** argv) {
    LoadClient app(argc, argv);
    app.start();
}
