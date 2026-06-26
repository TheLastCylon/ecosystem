#pragma once

#include <memory>
#include <vector>

#include <asio/awaitable.hpp>
#include <nlohmann/json.hpp>

#include "buffered_middleware_base.hpp"
#include "../data_transfer_objects/request_dto.hpp"
#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/middleware/buffered_middleware_manager.py's BufferedMiddlewareManager.
// Singleton -- access via BufferedMiddlewareManager::instance().
class BufferedMiddlewareManager {
public:
    static BufferedMiddlewareManager& instance() {
        static BufferedMiddlewareManager inst;
        return inst;
    }

    void add(std::shared_ptr<BufferedMiddlewareBase> middleware) {
        middlewares_.push_back(std::move(middleware));
    }

    // For tests: remove all registered middlewares.
    void clear() { middlewares_.clear(); }

    // Runs before_push for each middleware and merges the returned metadata
    // dicts (later middlewares can overwrite earlier ones on key collision,
    // same as Python's dict.update semantics).
    asio::awaitable<nlohmann::json> collect_push_metadata(const SpanKey& span_key, const RequestDTO& dto) {
        nlohmann::json metadata = nlohmann::json::object();
        for (auto& mw : middlewares_) {
            auto result = co_await mw->before_push(span_key, dto);
            if (!result.empty()) {
                metadata.update(result);
            }
        }
        co_return metadata;
    }

    asio::awaitable<void> run_before_process(
        const SpanKey& span_key, const RequestDTO& dto, const nlohmann::json& metadata, int retries)
    {
        for (auto& mw : middlewares_) {
            co_await mw->before_process(span_key, dto, metadata, retries);
        }
    }

    asio::awaitable<void> run_after_process(
        const SpanKey& span_key, const RequestDTO& dto, const nlohmann::json& metadata, bool success)
    {
        for (auto& mw : middlewares_) {
            co_await mw->after_process(span_key, dto, metadata, success);
        }
    }

private:
    BufferedMiddlewareManager() = default;
    std::vector<std::shared_ptr<BufferedMiddlewareBase>> middlewares_;
};
