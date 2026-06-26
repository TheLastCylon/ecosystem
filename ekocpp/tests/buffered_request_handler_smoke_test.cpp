#include <cstdio>
#include <filesystem>
#include <memory>

#include <asio/io_context.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>
#include <asio/use_awaitable.hpp>

#include "../src/requests/buffered_request_handler.hpp"
#include "../src/exceptions/exceptions.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

// push() is now a coroutine -- spawn it onto the io_context. Result is captured
// via a reference parameter inside the spawned lambda so span_key assertions can
// still be verified after io_context.run() drives it to completion.
void spawn_push(asio::io_context& io_context,
                std::shared_ptr<BufferedRequestHandler<std::function<bool(SpanKey, RequestDTO&)>>> buffered,
                int                 index,
                int*                span_key_hit_count = nullptr) {
    asio::co_spawn(io_context,
        [buffered, index, span_key_hit_count]() -> asio::awaitable<void> {
            RequestDTO     dto{nlohmann::json{{"i", index}}};
            RequestContext context{SpanKey::generate(), dto};
            auto result = co_await buffered->push(context);
            if (span_key_hit_count && result.contains("span_key")) {
                ++(*span_key_hit_count);
            }
        },
        asio::detached
    );
}

} // namespace

int main() {
    const std::string dir = "/tmp/ekocpp_buffered_handler_smoke_test";
    std::filesystem::remove_all(dir);
    std::filesystem::create_directories(dir);

    asio::io_context io_context(1);

    // --- Basic success path: push N items, all succeed first try, queue drains ---
    {
        using HandlerType = std::function<bool(SpanKey, RequestDTO&)>;
        int processed_count = 0;
        HandlerType handler = [&processed_count](SpanKey, RequestDTO& dto) -> bool {
            (void)dto;
            ++processed_count;
            return true;
        };

        auto buffered = std::make_shared<BufferedRequestHandler<HandlerType>>(
            io_context.get_executor(), "echo_buffered", handler, dir, "basic-endpoint", /*page_size=*/100, /*max_retries=*/3
        );
        buffered->unpause_receiving();
        buffered->unpause_processing();

        int span_key_count = 0;
        for (int i = 0; i < 5; ++i) {
            spawn_push(io_context, buffered, i, &span_key_count);
        }

        io_context.run();
        check(span_key_count == 5,     "push() returns an envelope with span_key for each call");
        check(processed_count == 5,    "all 5 pushed items processed by the background loop");
        check(buffered->pending_queue_size() == 0, "pending queue drained after run()");
        check(buffered->error_queue_size()   == 0, "no errors for a handler that always succeeds");

        io_context.restart();
    }

    // --- Retry then success: handler fails twice, succeeds on the 3rd attempt ---
    {
        using HandlerType = std::function<bool(SpanKey, RequestDTO&)>;
        int attempt_count = 0;
        HandlerType handler = [&attempt_count](SpanKey, RequestDTO&) -> bool {
            ++attempt_count;
            return attempt_count >= 3;
        };

        auto buffered = std::make_shared<BufferedRequestHandler<HandlerType>>(
            io_context.get_executor(), "retry_buffered", handler, dir, "retry-endpoint", /*page_size=*/100, /*max_retries=*/5
        );
        buffered->unpause_receiving();
        buffered->unpause_processing();

        asio::co_spawn(io_context,
            [buffered]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 1}}};
                RequestContext context{SpanKey::generate(), dto};
                co_await buffered->push(context);
            },
            asio::detached
        );

        io_context.run();

        check(attempt_count == 3,     "handler retried until success on attempt 3");
        check(buffered->pending_queue_size() == 0, "succeeded item removed from pending queue");
        check(buffered->error_queue_size()   == 0, "no error-queue entry for an eventually-successful item");

        io_context.restart();
    }

    // --- Max retries exceeded: routes to error queue, not an infinite retry loop ---
    {
        using HandlerType = std::function<bool(SpanKey, RequestDTO&)>;
        HandlerType handler = [](SpanKey, RequestDTO&) -> bool { return false; };

        auto buffered = std::make_shared<BufferedRequestHandler<HandlerType>>(
            io_context.get_executor(), "always_fails", handler, dir, "fail-endpoint", /*page_size=*/100, /*max_retries=*/2
        );
        buffered->unpause_receiving();
        buffered->unpause_processing();

        asio::co_spawn(io_context,
            [buffered]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 1}}};
                RequestContext context{SpanKey::generate(), dto};
                co_await buffered->push(context);
            },
            asio::detached
        );

        io_context.run();

        check(buffered->pending_queue_size() == 0, "pending queue empty after exhausting retries");
        check(buffered->error_queue_size()   == 1, "failed item routed to error queue after max_retries");

        io_context.restart();
    }

    // --- Receiving paused: push() throws ServerBusyException (status 500) ---
    {
        using HandlerType = std::function<bool(SpanKey, RequestDTO&)>;
        HandlerType handler = [](SpanKey, RequestDTO&) -> bool { return true; };
        auto buffered = std::make_shared<BufferedRequestHandler<HandlerType>>(
            io_context.get_executor(), "paused_buffered", handler, dir, "paused-endpoint"
        );
        // deliberately NOT calling unpause_receiving() -- starts paused, same as Python's default

        bool threw_busy = false;
        asio::co_spawn(io_context,
            [buffered, &threw_busy]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 1}}};
                RequestContext context{SpanKey::generate(), dto};
                try {
                    co_await buffered->push(context);
                } catch (const ServerBusyException& e) {
                    threw_busy = (e.status() == static_cast<int>(Status::APPLICATION_BUSY));
                }
            },
            asio::detached
        );
        io_context.run();
        check(threw_busy, "push() while receiving is paused throws ServerBusyException with APPLICATION_BUSY status");

        io_context.restart();
    }

    // --- Shutdown: pushes an item, then shuts down -- queue.shut_down() must
    //     be safely deferred until the in-flight processing loop actually exits.
    {
        using HandlerType = std::function<bool(SpanKey, RequestDTO&)>;
        HandlerType handler = [](SpanKey, RequestDTO&) -> bool { return true; };
        auto buffered = std::make_shared<BufferedRequestHandler<HandlerType>>(
            io_context.get_executor(), "shutdown_buffered", handler, dir, "shutdown-endpoint"
        );
        buffered->unpause_receiving();
        buffered->unpause_processing();

        asio::co_spawn(io_context,
            [buffered]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 1}}};
                RequestContext context{SpanKey::generate(), dto};
                co_await buffered->push(context);
            },
            asio::detached
        );

        bool shutdown_completed = false;
        asio::co_spawn(io_context, [buffered, &shutdown_completed]() -> asio::awaitable<void> {
            co_await buffered->shut_down();
            shutdown_completed = true;
        }, asio::detached);

        io_context.run();
        check(shutdown_completed, "shut_down() coroutine completed");
        check(buffered->is_receiving_paused() && buffered->is_processing_paused(), "shut_down pauses both receiving and processing");

        io_context.restart();
    }

    std::printf("\nAll buffered_request_handler smoke tests passed.\n");
    return 0;
}
