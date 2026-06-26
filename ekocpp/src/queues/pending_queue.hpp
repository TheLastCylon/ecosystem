#pragma once

#include <optional>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

#include "../data_transfer_objects/span_key.hpp"
#include "paginated_queue.hpp"

// Mirrors ekosis/queues/pending_queue.py's PendingEntry/ErrorEntry.
struct PendingEntry {
    SpanKey        span_key;
    int            retries = 0;
    nlohmann::json data;
    nlohmann::json metadata = nlohmann::json::object();

    nlohmann::json to_json() const {
        return {
            {"span_key", span_key.to_json()},
            {"retries", retries},
            {"data", data},
            {"metadata", metadata},
        };
    }

    static PendingEntry from_json(const nlohmann::json& j) {
        return PendingEntry{
            SpanKey::from_json(j.at("span_key")),
            j.value("retries", 0),
            j.at("data"),
            j.value("metadata", nlohmann::json::object()),
        };
    }
};

struct ErrorEntry {
    SpanKey        span_key;
    nlohmann::json data;
    std::string    reason;
    nlohmann::json metadata = nlohmann::json::object();

    nlohmann::json to_json() const {
        return {
            {"span_key", span_key.to_json()},
            {"data", data},
            {"reason", reason},
            {"metadata", metadata},
        };
    }

    static ErrorEntry from_json(const nlohmann::json& j) {
        return ErrorEntry{
            SpanKey::from_json(j.at("span_key")),
            j.at("data"),
            j.at("reason"),
            j.value("metadata", nlohmann::json::object()),
        };
    }
};

// Mirrors ekosis/queues/pending_queue.py's PendingQueue -- composes two
// PaginatedQueues (pending/error), each its own SQLite file, adding
// retry/error-routing business logic on top. Not a subclass of
// PaginatedQueue, same as the Python original.
//
// pop() deliberately returns the full PendingEntry (retries included) while
// the span-key-targeted pops/inspects return only the .data payload --
// this asymmetry is intentional, not an oversight: pop() feeds the
// buffered-handler retry loop, which needs the retry count; the span-key
// operations are for ad-hoc inspection/manual intervention, which only
// ever wants the payload back.
class PendingQueue {
public:
    PendingQueue(const std::string& directory, const std::string& file_basename, int page_size = 100)
        : pending_q(directory + "/" + file_basename + "-pending.sqlite", page_size),
          error_q(directory + "/" + file_basename + "-error.sqlite", page_size) {}

    void shut_down() {
        pending_q.shut_down();
        error_q.shut_down();
    }

    bool has_pending() const { return !pending_q.is_empty(); }
    size_t get_pending_size() const { return pending_q.size(); }
    size_t get_error_size() const { return error_q.size(); }

    nlohmann::json get_sizes() const {
        return {
            {"pending", get_pending_size()},
            {"error", get_error_size()},
        };
    }

    void move_all_error_to_pending() {
        while (error_q.size() > 0) {
            auto popped = error_q.pop();
            push_pending(popped->span_key, popped->data, 0, popped->metadata);
        }
    }

    std::optional<nlohmann::json> move_one_error_to_pending(const SpanKey& span_key) {
        auto popped = error_q.pop_span_key(span_key);
        if (!popped) return std::nullopt;
        push_pending(span_key, popped->data, 0, popped->metadata);
        return popped->data;
    }

    void clear_error_queue() { error_q.clear(); }

    std::vector<std::string> get_first_x_error_span_keys(size_t how_many = 1) const {
        return error_q.get_first_x_span_keys(how_many);
    }

    std::optional<nlohmann::json> pop_error_q_span_key(const SpanKey& span_key) {
        auto popped = error_q.pop_span_key(span_key);
        return popped ? std::optional<nlohmann::json>(popped->data) : std::nullopt;
    }

    std::optional<nlohmann::json> pop_pending_q_span_key(const SpanKey& span_key) {
        auto popped = pending_q.pop_span_key(span_key);
        return popped ? std::optional<nlohmann::json>(popped->data) : std::nullopt;
    }

    std::optional<nlohmann::json> inspect_error_q_span_key(const SpanKey& span_key) const {
        auto found = error_q.inspect_span_key(span_key);
        return found ? std::optional<nlohmann::json>(found->data) : std::nullopt;
    }

    std::optional<nlohmann::json> inspect_pending_q_span_key(const SpanKey& span_key) const {
        auto found = pending_q.inspect_span_key(span_key);
        return found ? std::optional<nlohmann::json>(found->data) : std::nullopt;
    }

    void push_pending(const SpanKey& span_key, const nlohmann::json& item_data, int retries = 0, const nlohmann::json& metadata = nlohmann::json::object()) {
        pending_q.push(PendingEntry{span_key, retries, item_data, metadata}, span_key);
    }

    void push_error(const SpanKey& span_key, const nlohmann::json& item_data, const std::string& reason, const nlohmann::json& metadata = nlohmann::json::object()) {
        spdlog::warn("Pushing message to error queue [{}] {}]", span_key.to_string(), reason);
        error_q.push(ErrorEntry{span_key, item_data, reason, metadata}, span_key);
    }

    std::optional<PendingEntry> pop() { return pending_q.pop(); }

    PaginatedQueue<PendingEntry> pending_q;
    PaginatedQueue<ErrorEntry>   error_q;
};
