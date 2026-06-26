#include <cstdio>
#include <string>
#include <vector>

#include <asio/io_context.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>

#include "../src/middleware/middleware_manager.hpp"
#include "../src/middleware/buffered_middleware_manager.hpp"
#include "../src/requests/request_router.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

// --- Concrete middleware implementations for testing ---

// Appends a tag to the dto's json so we can verify before_routing was called.
struct TaggingMiddleware : MiddlewareBase {
    std::string tag;
    explicit TaggingMiddleware(std::string t) : tag(std::move(t)) {}

    asio::awaitable<RequestDTO> before_routing(SpanKey, RequestDTO dto) override {
        dto.data["mw_tag"] = tag;
        co_return dto;
    }

    asio::awaitable<nlohmann::json> after_routing(SpanKey, nlohmann::json response) override {
        response["after_tag"] = tag;
        co_return response;
    }
};

// Ordering recorder: appends its name to a shared vector on each hook.
struct OrderRecorder : MiddlewareBase {
    std::string               name;
    std::vector<std::string>& log;
    OrderRecorder(std::string n, std::vector<std::string>& l) : name(std::move(n)), log(l) {}

    asio::awaitable<RequestDTO> before_routing(SpanKey, RequestDTO dto) override {
        log.push_back("before:" + name);
        co_return dto;
    }

    asio::awaitable<nlohmann::json> after_routing(SpanKey, nlohmann::json response) override {
        log.push_back("after:" + name);
        co_return response;
    }
};

// Buffered middleware that records before_push, before_process, after_process.
struct BufferedRecorder : BufferedMiddlewareBase {
    std::string               name;
    std::vector<std::string>& log;
    BufferedRecorder(std::string n, std::vector<std::string>& l) : name(std::move(n)), log(l) {}

    asio::awaitable<nlohmann::json> before_push(SpanKey, const RequestDTO&) override {
        log.push_back("push:" + name);
        co_return nlohmann::json{{"src", name}};
    }

    asio::awaitable<void> before_process(SpanKey, const RequestDTO&, const nlohmann::json&, int) override {
        log.push_back("before_process:" + name);
        co_return;
    }

    asio::awaitable<void> after_process(SpanKey, const RequestDTO&, const nlohmann::json&, bool success) override {
        log.push_back("after_process:" + name + (success ? ":ok" : ":fail"));
        co_return;
    }
};

// --- Helpers ---

RequestDTO echo_handler(SpanKey, RequestDTO& dto) { return dto; }

} // namespace

int main() {
    asio::io_context io_context(1);

    // =========================================================================
    // Regular middleware
    // =========================================================================

    // --- Empty chain: dto and response pass through unchanged ---
    {
        MiddlewareManager::instance().clear();
        RequestRouter router;
        router.register_endpoint("echo", echo_handler);

        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 42}}};
                RequestContext ctx{SpanKey::generate(), dto};
                result = co_await router.dispatch("echo", ctx);
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(result["status"] == static_cast<int>(Status::SUCCESS), "empty mw chain: SUCCESS status");
        check(result["data"]["x"] == 42,      "empty mw chain: original dto reaches handler");
        check(!result["data"].contains("mw_tag"), "empty mw chain: no mw_tag injected");
        check(!result["data"].contains("after_tag"), "empty mw chain: no after_tag injected");
    }

    // --- before_routing modifies dto before the handler sees it ---
    {
        MiddlewareManager::instance().clear();
        MiddlewareManager::instance().add(std::make_shared<TaggingMiddleware>("hello"));

        RequestRouter router;
        router.register_endpoint("echo", echo_handler);

        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 1}}};
                RequestContext ctx{SpanKey::generate(), dto};
                result = co_await router.dispatch("echo", ctx);
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(result["status"] == static_cast<int>(Status::SUCCESS), "tagging mw: SUCCESS status");
        check(result["data"]["mw_tag"] == "hello",   "before_routing: mw_tag injected into dto, seen by handler");
        check(result["data"]["after_tag"] == "hello", "after_routing: after_tag injected into response");
    }

    // --- Multiple middlewares run in registration order ---
    {
        MiddlewareManager::instance().clear();
        std::vector<std::string> log;
        MiddlewareManager::instance().add(std::make_shared<OrderRecorder>("A", log));
        MiddlewareManager::instance().add(std::make_shared<OrderRecorder>("B", log));

        RequestRouter router;
        router.register_endpoint("echo", echo_handler);

        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"x", 0}}};
                RequestContext ctx{SpanKey::generate(), dto};
                co_await router.dispatch("echo", ctx);
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(log.size() == 4, "two middlewares: 4 hook calls total");
        check(log[0] == "before:A" && log[1] == "before:B", "before_routing runs A then B");
        check(log[2] == "after:A"  && log[3] == "after:B",  "after_routing runs A then B");
    }

    // --- Middleware does NOT run for unknown route keys ---
    {
        MiddlewareManager::instance().clear();
        std::vector<std::string> log;
        MiddlewareManager::instance().add(std::make_shared<OrderRecorder>("C", log));

        RequestRouter router;

        nlohmann::json result;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{}};
                RequestContext ctx{SpanKey::generate(), dto};
                result = co_await router.dispatch("does_not_exist", ctx);
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(result["status"] == static_cast<int>(Status::ROUTE_KEY_UNKNOWN), "unknown route: ROUTE_KEY_UNKNOWN");
        check(log.empty(), "unknown route: middleware is not invoked");
        MiddlewareManager::instance().clear();
    }

    // =========================================================================
    // Buffered middleware
    // =========================================================================

    // --- collect_push_metadata: empty chain returns empty object ---
    {
        BufferedMiddlewareManager::instance().clear();

        nlohmann::json meta;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO dto{nlohmann::json{{"x", 1}}};
                meta = co_await BufferedMiddlewareManager::instance().collect_push_metadata(
                    SpanKey::generate(), dto
                );
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(meta.is_object() && meta.empty(), "buffered empty chain: collect_push_metadata returns empty object");
    }

    // --- collect_push_metadata merges dicts from multiple middlewares ---
    {
        BufferedMiddlewareManager::instance().clear();
        std::vector<std::string> log;
        BufferedMiddlewareManager::instance().add(std::make_shared<BufferedRecorder>("X", log));
        BufferedMiddlewareManager::instance().add(std::make_shared<BufferedRecorder>("Y", log));

        nlohmann::json meta;
        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO dto{nlohmann::json{{"v", 7}}};
                meta = co_await BufferedMiddlewareManager::instance().collect_push_metadata(
                    SpanKey::generate(), dto
                );
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(log[0] == "push:X" && log[1] == "push:Y", "collect_push_metadata calls before_push in order");
        // both middlewares return {"src": <name>}; Y's value overwrites X's since they share the key
        check(meta["src"] == "Y", "collect_push_metadata merges dicts (later overrides on collision)");
    }

    // --- before_process / after_process called in order around the handler ---
    {
        BufferedMiddlewareManager::instance().clear();
        std::vector<std::string> log;
        BufferedMiddlewareManager::instance().add(std::make_shared<BufferedRecorder>("P", log));

        asio::co_spawn(io_context,
            [&]() -> asio::awaitable<void> {
                RequestDTO     dto{nlohmann::json{{"k", 1}}};
                SpanKey        sk  = SpanKey::generate();
                nlohmann::json meta = nlohmann::json::object();
                co_await BufferedMiddlewareManager::instance().run_before_process(sk, dto, meta, 0);
                co_await BufferedMiddlewareManager::instance().run_after_process(sk, dto, meta, true);
            },
            asio::detached
        );
        io_context.run(); io_context.restart();

        check(log.size() == 2, "buffered hooks: 2 calls total");
        check(log[0] == "before_process:P",   "before_process called");
        check(log[1] == "after_process:P:ok", "after_process called with success=true");
        BufferedMiddlewareManager::instance().clear();
    }

    std::printf("\nAll middleware smoke tests passed.\n");
    return 0;
}
