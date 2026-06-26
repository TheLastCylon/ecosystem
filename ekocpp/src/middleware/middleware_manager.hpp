#pragma once

#include <memory>
#include <vector>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "middleware_base.hpp"
#include "../data_transfer_objects/request_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/middleware/manager.py's MiddlewareManager.
// Singleton -- access via MiddlewareManager::instance().
// Call add() at startup (before any requests are processed) to register
// concrete middleware implementations; they run in registration order.
class MiddlewareManager {
public:
    static MiddlewareManager& instance() {
        static MiddlewareManager inst;
        return inst;
    }

    void add(std::shared_ptr<MiddlewareBase> middleware) {
        middlewares_.push_back(std::move(middleware));
    }

    // For tests: remove all registered middlewares.
    void clear() { middlewares_.clear(); }

    // Runs each middleware's before_routing in order, threading the dto through
    // the chain. Returns the final dto, which is what the handler will receive.
    asio::awaitable<RequestDTO> run_before_routing(SpanKey span_key, RequestDTO dto) {
        for (auto& mw : middlewares_) {
            dto = co_await mw->before_routing(span_key, std::move(dto));
        }
        co_return dto;
    }

    // Runs each middleware's after_routing in order, threading the response data
    // through the chain. Returns the final response data, which is then wrapped
    // in the {status, data} envelope by dispatch().
    asio::awaitable<nlohmann::json> run_after_routing(SpanKey span_key, nlohmann::json response) {
        for (auto& mw : middlewares_) {
            response = co_await mw->after_routing(span_key, std::move(response));
        }
        co_return response;
    }

private:
    MiddlewareManager() = default;
    std::vector<std::shared_ptr<MiddlewareBase>> middlewares_;
};
