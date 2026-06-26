#pragma once

#include <list>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include <nlohmann/json.hpp>

#include "../data_transfer_objects/span_key.hpp"

// Mirrors ekosis/queues/paginated_queue.py's QueuePage -- an in-memory FIFO
// page of queued entries, keyed by SpanKey for O(1) lookup/erase by key in
// addition to front/back access.
//
// QueuedType contract: needs `nlohmann::json to_json() const` and a static
// `QueuedType from_json(const nlohmann::json&)` -- the same manual
// to_json()/from_json() convention already used by ekocpp's other DTOs
// (see otlp_log_record.hpp), not the NLOHMANN_DEFINE_TYPE macro.
//
// std::list (not std::vector) + an iterator-valued index map is the one real
// departure from a literal port: Python's pop_entry/PaginatedQueue.pop_entry
// does a linear scan to find an entry's position before erasing it
// (paginated_queue.py:96-101). A list's iterators stay valid across
// insertions/erasures elsewhere in the list, so the index map can point
// straight at the node to erase -- same FIFO ordering and observable
// behaviour, O(1) erase-by-key instead of O(n).
template <typename QueuedType>
class QueuePage {
public:
    struct PageEntry {
        SpanKey     span_key;
        std::string object_string;
    };

    SpanKey push(const QueuedType& object, const SpanKey& span_key) {
        return push_back(object, span_key);
    }

    SpanKey push_back(const QueuedType& object, const SpanKey& span_key) {
        return push_with_str(object.to_json().dump(), span_key);
    }

    SpanKey push_with_str(const std::string& object_string, const SpanKey& span_key) {
        entries_.push_back(PageEntry{span_key, object_string});
        index_[span_key] = std::prev(entries_.end());
        return span_key;
    }

    std::optional<QueuedType> pop() { return pop_front(); }

    std::optional<QueuedType> pop_front() {
        if (entries_.empty()) return std::nullopt;
        PageEntry entry = std::move(entries_.front());
        entries_.pop_front();
        index_.erase(entry.span_key);
        return entry_to_object(entry);
    }

    size_t size() const { return entries_.size(); }

    bool has_entry(const SpanKey& span_key) const {
        return index_.find(span_key) != index_.end();
    }

    std::optional<QueuedType> inspect_entry(const SpanKey& span_key) const {
        auto it = index_.find(span_key);
        if (it == index_.end()) return std::nullopt;
        return entry_to_object(*it->second);
    }

    std::optional<QueuedType> pop_entry(const SpanKey& span_key) {
        auto it = index_.find(span_key);
        if (it == index_.end()) return std::nullopt;
        PageEntry entry = std::move(*it->second);
        entries_.erase(it->second);
        index_.erase(it);
        return entry_to_object(entry);
    }

    std::vector<std::string> get_first_x_span_keys(size_t how_many) const {
        std::vector<std::string> result;
        for (const auto& entry : entries_) {
            if (result.size() >= how_many) break;
            result.push_back(entry.span_key.to_string());
        }
        return result;
    }

    // For PaginatedQueue::write_front_page/write_back_page to iterate when
    // flushing this page to disk -- read-only, the page itself gets replaced
    // by a fresh empty one right after, same as the Python original.
    const std::list<PageEntry>& entries() const { return entries_; }

private:
    std::list<PageEntry>                                                 entries_;
    std::unordered_map<SpanKey, typename std::list<PageEntry>::iterator> index_;

    static QueuedType entry_to_object(const PageEntry& entry) {
        return QueuedType::from_json(nlohmann::json::parse(entry.object_string));
    }
};
