#pragma once

#include <list>
#include <optional>
#include <unordered_map>
#include <utility>
#include <vector>

// Mirrors ekosis/cacheing/lru_cache.py's LRUCache -- a fixed-capacity,
// in-memory least-recently-used cache.
//
// Python hand-rolls a circular doubly-linked list of fixed slots (head/tail/
// previous/next pointers) plus a dict index, purely to avoid allocation
// churn on eviction -- the same problem QueuePage solved for queued entries.
// Here too, std::list (front = MRU, back = LRU) + an iterator-valued index
// map replaces the hand-rolled pointer surgery: std::list::splice relocates
// an existing node to front/back in O(1) with no new allocation, so eviction
// and promotion both collapse to one splice call each.
//
// pop() removes the MOST-recently-used entry (front), not the LRU one --
// confirmed against lru_cache.py's own test (fill '10'..'19', pop() returns
// '19'). It's a stack-pop on recency order, not an eviction primitive --
// preserved exactly, not "fixed" to look more like eviction.
template <typename Key, typename Value>
class LRUCache {
public:
    explicit LRUCache(size_t max_size) : max_size_(max_size) {}

    void set(const Key& key, const Value& value) {
        auto it = index_.find(key);
        if (it != index_.end()) {
            it->second->second = value;
            entries_.splice(entries_.begin(), entries_, it->second);
            return;
        }

        if (entries_.size() < max_size_) {
            entries_.emplace_front(key, value);
            index_[key] = entries_.begin();
            return;
        }

        auto lru_it = std::prev(entries_.end());
        index_.erase(lru_it->first);
        lru_it->first  = key;
        lru_it->second = value;
        entries_.splice(entries_.begin(), entries_, lru_it);
        index_[key] = entries_.begin();
    }

    // does not affect cache order
    std::optional<Value> peek(const Key& key) const {
        auto it = index_.find(key);
        if (it == index_.end()) return std::nullopt;
        return it->second->second;
    }

    // alters cache order -- moves key to front
    std::optional<Value> get(const Key& key) {
        auto it = index_.find(key);
        if (it == index_.end()) return std::nullopt;
        entries_.splice(entries_.begin(), entries_, it->second);
        return it->second->second;
    }

    std::optional<Value> pop_item(const Key& key) {
        auto it = index_.find(key);
        if (it == index_.end()) return std::nullopt;
        Value value = std::move(it->second->second);
        entries_.erase(it->second);
        index_.erase(it);
        return value;
    }

    // removes the most-recently-used entry (front), not the LRU one
    std::optional<std::pair<Key, Value>> pop() {
        if (entries_.empty()) return std::nullopt;
        std::pair<Key, Value> front = std::move(entries_.front());
        index_.erase(front.first);
        entries_.pop_front();
        return front;
    }

    void erase(const Key& key) {
        auto it = index_.find(key);
        if (it == index_.end()) return;
        entries_.erase(it->second);
        index_.erase(it);
    }

    void clear() {
        entries_.clear();
        index_.clear();
    }

    bool contains(const Key& key) const { return index_.find(key) != index_.end(); }

    size_t size() const { return entries_.size(); }

    // MRU -> LRU order, matching Python's head-first iteration
    std::vector<Key> keys() const {
        std::vector<Key> result;
        result.reserve(entries_.size());
        for (const auto& entry : entries_) result.push_back(entry.first);
        return result;
    }

    std::vector<Value> values() const {
        std::vector<Value> result;
        result.reserve(entries_.size());
        for (const auto& entry : entries_) result.push_back(entry.second);
        return result;
    }

    std::vector<std::pair<Key, Value>> items() const {
        return std::vector<std::pair<Key, Value>>(entries_.begin(), entries_.end());
    }

private:
    size_t                                                                      max_size_;
    std::list<std::pair<Key, Value>>                                            entries_;
    std::unordered_map<Key, typename std::list<std::pair<Key, Value>>::iterator> index_;
};
