#include <cstdio>

#include <asio/io_context.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>

#include "../src/requests/request_router.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

RequestDTO ok_handler(SpanKey, RequestDTO& dto)              { return dto; }
RequestDTO processing_failure_handler(SpanKey, RequestDTO&)  { throw ApplicationProcessingException("disk is full"); }
RequestDTO server_busy_handler(SpanKey, RequestDTO&)         { throw ServerBusyException("paused for maintenance"); }

} // namespace

int main() {
    asio::io_context io_context(1);

    RequestRouter router;
    router.register_endpoint("ok",              ok_handler);
    router.register_endpoint("fails_processing", processing_failure_handler);
    router.register_endpoint("busy",             server_busy_handler);

    RequestDTO     dto{nlohmann::json{{"x", 1}}};
    RequestContext context{SpanKey::generate(), dto};

    // --- Successful dispatch ---
    {
        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> { result = co_await router.dispatch("ok", context); },
            asio::detached
        );
        io_context.run();
        io_context.restart();
        check(result["status"] == static_cast<int>(Status::SUCCESS), "successful dispatch returns SUCCESS status");
        check(result["data"]["x"] == 1, "successful dispatch returns the handler's data");
    }

    // --- Unknown route key ---
    {
        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> { result = co_await router.dispatch("does_not_exist", context); },
            asio::detached
        );
        io_context.run();
        io_context.restart();
        check(result["status"] == static_cast<int>(Status::ROUTE_KEY_UNKNOWN), "unknown route_key maps to ROUTE_KEY_UNKNOWN");
        check(result["data"].get<std::string>().find("does_not_exist") != std::string::npos, "unknown route_key message names the route");
    }

    // --- ApplicationProcessingException caught inside dispatch() ---
    {
        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> { result = co_await router.dispatch("fails_processing", context); },
            asio::detached
        );
        io_context.run();
        io_context.restart();
        check(result["status"] == static_cast<int>(Status::PROCESSING_FAILURE), "ApplicationProcessingException maps to PROCESSING_FAILURE, caught inside dispatch()");
        check(result["data"].get<std::string>().find("disk is full") != std::string::npos, "the original exception message is preserved");
        check(result["data"].get<std::string>().find("fails_processing") != std::string::npos, "the message names the route_key, matching Python's RouterProcessingException format");
    }

    // --- ResponseException subtypes propagate out of dispatch() uncaught ---
    // dispatch() only catches ApplicationProcessingException; ServerBusyException
    // (a ResponseException) propagates through co_await to the caller.
    {
        bool propagated = false;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                try {
                    co_await router.dispatch("busy", context);
                } catch (const ServerBusyException&) {
                    propagated = true;
                }
            },
            asio::detached
        );
        io_context.run();
        io_context.restart();
        check(propagated, "ServerBusyException (a ResponseException, not ApplicationProcessingException) propagates out of dispatch() uncaught");
    }

    std::printf("\nAll request_router_exception smoke tests passed.\n");
    return 0;
}
