#pragma once

#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <SQLiteCpp/SQLiteCpp.h>
#include <nlohmann/json.hpp>

#include "../data_transfer_objects/span_key.hpp"
#include "queue_page.hpp"

// Mirrors ekosis/queues/paginated_queue.py's PaginatedQueue -- two in-memory
// QueuePages (front/back) with a SQLite-backed overflow in between, so a
// queue with millions of entries doesn't have to live entirely in RAM.
//
// The record_id sign trick (load-bearing, not incidental): front-page
// flushes get DESCENDING negative ids (min-1, min-2, ...), back-page
// flushes get ASCENDING positive ids (max+1, max+2, ...). That's why
// `ORDER BY record_id ASC` alone reconstructs true FIFO order even though
// front and back pages get written at completely different times by
// completely different code paths -- the sign of the id encodes "head of
// queue" vs. "tail of queue" without a separate ordering column.
//
// front_page_/back_page_ are shared_ptr, not plain values, specifically to
// mirror Python's `self.back_page is self.front_page` identity check --
// at construction (and whenever the queue drains back to one page) both
// names alias the SAME QueuePage object; later they diverge to two distinct
// pages. A shared_ptr is the direct C++ translation of that aliasing, not
// an ownership-sharing convenience.
//
// Synchronous throughout, unlike Python's `async def` -- those coroutines
// never actually suspend on anything async (SQLite here is blocking, in-
// memory page ops are instant); Python wrapped them in async purely so
// ekosis's async call sites could await them uniformly. ekocpp has no such
// constraint (see StateStore in ekosis_log_shipper for the same precedent).
template <typename QueuedType>
class PaginatedQueue {
public:
    PaginatedQueue(std::string file_path, int page_size = 100)
        : file_path_(std::move(file_path)),
          page_size_(page_size),
          db_(file_path_, SQLite::OPEN_READWRITE | SQLite::OPEN_CREATE) {
        db_.exec(
            "CREATE TABLE IF NOT EXISTS queued_objects ("
            "  record_id     INTEGER PRIMARY KEY,"
            "  span_key      BLOB UNIQUE NOT NULL,"
            "  object_string TEXT NOT NULL"
            ")"
        );
        front_page_ = std::make_shared<QueuePage<QueuedType>>();
        back_page_  = front_page_;
        do_initial_load();
    }

    SpanKey push(const QueuedType& object, const SpanKey& span_key) {
        if (back_page_->has_entry(span_key) || front_page_->has_entry(span_key) || record_exists(span_key)) {
            return span_key;
        }
        if (back_page_->size() < static_cast<size_t>(page_size_)) {
            return back_page_->push(object, span_key);
        }
        if (back_page_ == front_page_) {
            back_page_ = std::make_shared<QueuePage<QueuedType>>();
            return back_page_->push(object, span_key);
        }
        write_back_page();
        return back_page_->push(object, span_key);
    }

    std::optional<QueuedType> pop() {
        if (front_page_->size() > 0) {
            return front_page_->pop();
        }
        if (database_size() > 0) {
            load_front_page();
            return front_page_->pop();
        }
        if (back_page_->size() > 0) {
            front_page_ = back_page_;
            return front_page_->pop();
        }
        front_page_ = back_page_;
        return std::nullopt;
    }

    size_t size() const {
        size_t total = static_cast<size_t>(database_size());
        if (front_page_ == back_page_) {
            total += front_page_->size();
        } else {
            total += front_page_->size() + back_page_->size();
        }
        return total;
    }

    bool is_empty() const { return size() == 0; }

    std::optional<QueuedType> inspect_span_key(const SpanKey& span_key) const {
        if (auto found = front_page_->inspect_entry(span_key)) return found;
        if (auto found = back_page_->inspect_entry(span_key)) return found;
        const auto record = get_record_by_span_key(span_key);
        if (!record) return std::nullopt;
        return QueuedType::from_json(nlohmann::json::parse(record->object_string));
    }

    std::optional<QueuedType> pop_span_key(const SpanKey& span_key) {
        if (auto found = front_page_->pop_entry(span_key)) return found;
        if (auto found = back_page_->pop_entry(span_key)) return found;
        const auto record = get_record_by_span_key(span_key);
        if (!record) return std::nullopt;
        delete_record_ids({record->record_id});
        return QueuedType::from_json(nlohmann::json::parse(record->object_string));
    }

    // Fixes ekosis/queues/paginated_queue.py's flagged bug (comment at
    // paginated_queue.py:318-322): the Python original only inspects the
    // front page, missing entries split across front page/DB/back page.
    // Here: front page first, then the DB's true FIFO order (ORDER BY
    // record_id ASC -- see the record_id sign trick above), then the back
    // page if it's a genuinely distinct page -- all read-only, no deletes.
    std::vector<std::string> get_first_x_span_keys(size_t how_many) const {
        std::vector<std::string> result = front_page_->get_first_x_span_keys(how_many);
        if (result.size() >= how_many) return result;

        SQLite::Statement query(db_, "SELECT span_key FROM queued_objects ORDER BY record_id ASC LIMIT ?");
        query.bind(1, static_cast<int64_t>(how_many - result.size()));
        while (query.executeStep()) {
            const auto* blob = static_cast<const uint8_t*>(query.getColumn(0).getBlob());
            result.push_back(SpanKey::from_bytes(blob).to_string());
        }
        if (result.size() >= how_many || back_page_ == front_page_) return result;

        const auto back_keys = back_page_->get_first_x_span_keys(how_many - result.size());
        result.insert(result.end(), back_keys.begin(), back_keys.end());
        return result;
    }

    void clear() {
        db_.exec("DELETE FROM queued_objects");
        front_page_ = std::make_shared<QueuePage<QueuedType>>();
        back_page_  = front_page_;
    }

    void shut_down() {
        if (front_page_ == back_page_) {
            if (front_page_->size() > 0) write_front_page();
        } else {
            if (front_page_->size() > 0) write_front_page();
            if (back_page_->size() > 0) write_back_page();
        }
    }

private:
    struct DbRecord {
        int64_t     record_id;
        std::string object_string;
    };

    std::string                            file_path_;
    int                                    page_size_;
    mutable SQLite::Database               db_;
    std::shared_ptr<QueuePage<QueuedType>> front_page_;
    std::shared_ptr<QueuePage<QueuedType>> back_page_;

    void do_initial_load() {
        if (database_size() > 0) {
            load_front_page();
        }
        if (database_size() > 0) { // still data left after loading the front page
            back_page_ = std::make_shared<QueuePage<QueuedType>>();
            load_back_page();
        }
    }

    int64_t database_size() const {
        SQLite::Statement query(db_, "SELECT COUNT(*) FROM queued_objects");
        query.executeStep();
        return query.getColumn(0).getInt64();
    }

    int64_t max_record_id() const {
        if (database_size() < 1) return 0;
        SQLite::Statement query(db_, "SELECT MAX(record_id) FROM queued_objects");
        query.executeStep();
        return query.getColumn(0).getInt64();
    }

    int64_t min_record_id() const {
        if (database_size() < 1) return 0;
        SQLite::Statement query(db_, "SELECT MIN(record_id) FROM queued_objects");
        query.executeStep();
        return query.getColumn(0).getInt64();
    }

    void delete_record_ids(const std::vector<int64_t>& record_ids) {
        if (record_ids.empty()) return;
        std::string placeholders;
        for (size_t i = 0; i < record_ids.size(); ++i) {
            placeholders += (i == 0 ? "?" : ",?");
        }
        SQLite::Statement stmt(db_, "DELETE FROM queued_objects WHERE record_id IN (" + placeholders + ")");
        for (size_t i = 0; i < record_ids.size(); ++i) {
            stmt.bind(static_cast<int>(i + 1), record_ids[i]);
        }
        stmt.exec();
    }

    void load_front_page() {
        SQLite::Statement query(db_, "SELECT record_id, span_key, object_string FROM queued_objects ORDER BY record_id ASC LIMIT ?");
        query.bind(1, page_size_);

        std::vector<int64_t> ids_to_delete;
        while (query.executeStep()) {
            ids_to_delete.push_back(query.getColumn(0).getInt64());
            const auto* blob = static_cast<const uint8_t*>(query.getColumn(1).getBlob());
            front_page_->push_with_str(query.getColumn(2).getString(), SpanKey::from_bytes(blob));
        }
        delete_record_ids(ids_to_delete);
    }

    void load_back_page() {
        SQLite::Statement query(db_, "SELECT record_id, span_key, object_string FROM queued_objects ORDER BY record_id DESC LIMIT ?");
        query.bind(1, page_size_);

        std::vector<int64_t> ids_to_delete;
        while (query.executeStep()) {
            ids_to_delete.push_back(query.getColumn(0).getInt64());
            const auto* blob = static_cast<const uint8_t*>(query.getColumn(1).getBlob());
            back_page_->push_with_str(query.getColumn(2).getString(), SpanKey::from_bytes(blob));
        }
        delete_record_ids(ids_to_delete);
    }

    // Newest-of-front-page first (closest to zero), decreasing -- mirrors
    // Python's `reversed(front_page.get_page_list())` walk.
    void write_front_page() {
        int64_t next_id = min_record_id() - 1;
        SQLite::Statement stmt(db_, "INSERT INTO queued_objects (record_id, span_key, object_string) VALUES (?, ?, ?)");
        const auto& entries = front_page_->entries();
        for (auto it = entries.rbegin(); it != entries.rend(); ++it) {
            const auto bytes = it->span_key.to_bytes();
            stmt.bind(1, next_id);
            stmt.bind(2, bytes.data(), static_cast<int>(bytes.size()));
            stmt.bind(3, it->object_string);
            stmt.exec();
            stmt.reset();
            --next_id;
        }
        front_page_ = std::make_shared<QueuePage<QueuedType>>();
    }

    // Oldest-of-back-page first, increasing -- arrival order stays
    // chronological.
    void write_back_page() {
        int64_t next_id = max_record_id() + 1;
        SQLite::Statement stmt(db_, "INSERT INTO queued_objects (record_id, span_key, object_string) VALUES (?, ?, ?)");
        for (const auto& entry : back_page_->entries()) {
            const auto bytes = entry.span_key.to_bytes();
            stmt.bind(1, next_id);
            stmt.bind(2, bytes.data(), static_cast<int>(bytes.size()));
            stmt.bind(3, entry.object_string);
            stmt.exec();
            stmt.reset();
            ++next_id;
        }
        back_page_ = std::make_shared<QueuePage<QueuedType>>();
    }

    bool record_exists(const SpanKey& span_key) const {
        SQLite::Statement query(db_, "SELECT EXISTS(SELECT 1 FROM queued_objects WHERE span_key = ?)");
        const auto bytes = span_key.to_bytes();
        query.bind(1, bytes.data(), static_cast<int>(bytes.size()));
        query.executeStep();
        return query.getColumn(0).getInt() != 0;
    }

    std::optional<DbRecord> get_record_by_span_key(const SpanKey& span_key) const {
        SQLite::Statement query(db_, "SELECT record_id, object_string FROM queued_objects WHERE span_key = ?");
        const auto bytes = span_key.to_bytes();
        query.bind(1, bytes.data(), static_cast<int>(bytes.size()));
        if (query.executeStep()) {
            return DbRecord{query.getColumn(0).getInt64(), query.getColumn(1).getString()};
        }
        return std::nullopt;
    }
};
