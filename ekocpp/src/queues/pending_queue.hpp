#pragma once

#include <mutex>
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
        : pending_q_(directory + "/" + file_basename + "-pending.sqlite", page_size),
          error_q_(directory + "/" + file_basename + "-error.sqlite", page_size) {}

    void shut_down() {
        std::scoped_lock lock(mutex_);
        pending_q_.shut_down();
        error_q_.shut_down();
    }

    bool   has_pending()      const { std::scoped_lock lock(mutex_); return !pending_q_.is_empty(); }
    size_t get_pending_size() const { std::scoped_lock lock(mutex_); return pending_q_.size(); }
    size_t get_error_size()   const { std::scoped_lock lock(mutex_); return error_q_.size(); }

    nlohmann::json get_sizes() const {
        std::scoped_lock lock(mutex_);
        return {
            {"pending", pending_q_.size()},
            {"error",   error_q_.size()},
        };
    }

    void move_all_error_to_pending() {
        std::scoped_lock lock(mutex_);
        while (error_q_.size() > 0) {
            auto popped = error_q_.pop();
            push_pending_unlocked(popped->span_key, popped->data, 0, popped->metadata);
        }
    }

    std::optional<nlohmann::json> move_one_error_to_pending(const SpanKey& span_key) {
        std::scoped_lock lock(mutex_);
        auto popped = error_q_.pop_span_key(span_key);
        if (!popped) return std::nullopt;
        push_pending_unlocked(span_key, popped->data, 0, popped->metadata);
        return popped->data;
    }

    void clear_error_queue() { std::scoped_lock lock(mutex_); error_q_.clear(); }

    std::vector<std::string> get_first_x_error_span_keys(size_t how_many = 1) const {
        std::scoped_lock lock(mutex_);
        return error_q_.get_first_x_span_keys(how_many);
    }

    std::optional<nlohmann::json> pop_error_q_span_key(const SpanKey& span_key) {
        std::scoped_lock lock(mutex_);
        auto popped = error_q_.pop_span_key(span_key);
        return popped ? std::optional<nlohmann::json>(popped->data) : std::nullopt;
    }

    std::optional<nlohmann::json> pop_pending_q_span_key(const SpanKey& span_key) {
        std::scoped_lock lock(mutex_);
        auto popped = pending_q_.pop_span_key(span_key);
        return popped ? std::optional<nlohmann::json>(popped->data) : std::nullopt;
    }

    std::optional<nlohmann::json> inspect_error_q_span_key(const SpanKey& span_key) const {
        std::scoped_lock lock(mutex_);
        auto found = error_q_.inspect_span_key(span_key);
        return found ? std::optional<nlohmann::json>(found->data) : std::nullopt;
    }

    std::optional<nlohmann::json> inspect_pending_q_span_key(const SpanKey& span_key) const {
        std::scoped_lock lock(mutex_);
        auto found = pending_q_.inspect_span_key(span_key);
        return found ? std::optional<nlohmann::json>(found->data) : std::nullopt;
    }

    void push_pending(const SpanKey& span_key, const nlohmann::json& item_data, int retries = 0, const nlohmann::json& metadata = nlohmann::json::object()) {
        std::scoped_lock lock(mutex_);
        push_pending_unlocked(span_key, item_data, retries, metadata);
    }

    void push_error(const SpanKey& span_key, const nlohmann::json& item_data, const std::string& reason, const nlohmann::json& metadata = nlohmann::json::object()) {
        spdlog::warn("Pushing message to error queue [{}] {}]", span_key.to_string(), reason);
        std::scoped_lock lock(mutex_);
        error_q_.push(ErrorEntry{span_key, item_data, reason, metadata}, span_key);
    }

    std::optional<PendingEntry> pop() {
        std::scoped_lock lock(mutex_);
        return pending_q_.pop();
    }

private:
    void push_pending_unlocked(const SpanKey& span_key, const nlohmann::json& item_data, int retries, const nlohmann::json& metadata) {
        pending_q_.push(PendingEntry{span_key, retries, item_data, metadata}, span_key);
    }

    mutable std::mutex           mutex_;
    PaginatedQueue<PendingEntry> pending_q_;
    PaginatedQueue<ErrorEntry>   error_q_;
};
