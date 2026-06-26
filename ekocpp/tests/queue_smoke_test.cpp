#include <cassert>
#include <cstdio>
#include <filesystem>

#include "../src/queues/pending_queue.hpp"

namespace {

// Mirrors the basic JSON DTO contract every QueuedType needs --
// to_json()/from_json(), nothing else.
struct TestPayload {
    std::string message;

    nlohmann::json to_json() const { return {{"message", message}}; }
    static TestPayload from_json(const nlohmann::json& j) { return TestPayload{j.at("message")}; }
};

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

} // namespace

int main() {
    const std::string dir = "/tmp/ekocpp_queue_smoke_test";
    std::filesystem::remove_all(dir);
    std::filesystem::create_directories(dir);

    // --- PaginatedQueue: basic FIFO order, small page_size to force overflow paging ---
    {
        PaginatedQueue<TestPayload> queue(dir + "/basic.sqlite", /*page_size=*/2);

        std::vector<SpanKey> keys;
        for (int i = 0; i < 7; ++i) {
            const SpanKey key = SpanKey::generate();
            keys.push_back(key);
            queue.push(TestPayload{"msg-" + std::to_string(i)}, key);
        }
        check(queue.size() == 7, "pushed 7 entries, size() == 7");

        // FIFO order preserved across the front/DB/back split (page_size=2
        // forces real overflow -- this is exercising the record_id sign trick).
        for (int i = 0; i < 7; ++i) {
            auto popped = queue.pop();
            check(popped.has_value(), ("pop() returns a value for entry " + std::to_string(i)).c_str());
            check(popped->message == "msg-" + std::to_string(i), ("FIFO order preserved at index " + std::to_string(i)).c_str());
        }
        check(!queue.pop().has_value(), "pop() on drained queue returns nullopt");
    }

    // --- Persistence across restart (overflow rows survive a close+reopen) ---
    {
        PaginatedQueue<TestPayload> queue(dir + "/restart.sqlite", /*page_size=*/2);
        for (int i = 0; i < 5; ++i) {
            queue.push(TestPayload{"persist-" + std::to_string(i)}, SpanKey::generate());
        }
        queue.shut_down();
    }
    {
        PaginatedQueue<TestPayload> queue(dir + "/restart.sqlite", /*page_size=*/2);
        check(queue.size() == 5, "size survives a close+reopen (overflow rows persisted)");
        auto popped = queue.pop();
        check(popped.has_value() && popped->message == "persist-0", "FIFO order survives close+reopen");
    }

    // --- inspect/pop by span_key, across front page / DB / back page ---
    {
        PaginatedQueue<TestPayload> queue(dir + "/spankey.sqlite", /*page_size=*/2);
        std::vector<SpanKey> keys;
        for (int i = 0; i < 6; ++i) {
            const SpanKey key = SpanKey::generate();
            keys.push_back(key);
            queue.push(TestPayload{"sk-" + std::to_string(i)}, key);
        }
        // keys[0] should be in the DB (paged out), keys[5] should be in the back page.
        auto inspected_db = queue.inspect_span_key(keys[0]);
        check(inspected_db.has_value() && inspected_db->message == "sk-0", "inspect_span_key finds a DB-overflowed entry");
        auto inspected_back = queue.inspect_span_key(keys[5]);
        check(inspected_back.has_value() && inspected_back->message == "sk-5", "inspect_span_key finds a back-page entry");

        auto popped = queue.pop_span_key(keys[0]);
        check(popped.has_value() && popped->message == "sk-0", "pop_span_key removes a DB-overflowed entry");
        check(queue.size() == 5, "size() decremented after pop_span_key");
        check(!queue.inspect_span_key(keys[0]).has_value(), "popped entry no longer inspectable");
    }

    // --- get_first_x_span_keys bug fix: entries split across front/DB/back ---
    {
        PaginatedQueue<TestPayload> queue(dir + "/firstx.sqlite", /*page_size=*/2);
        std::vector<SpanKey> keys;
        for (int i = 0; i < 6; ++i) {
            const SpanKey key = SpanKey::generate();
            keys.push_back(key);
            queue.push(TestPayload{"fx-" + std::to_string(i)}, key);
        }
        // With page_size=2: front page never repopulated (still empty until a pop),
        // so entries are split between DB (paged-out middle) and back page (newest 2).
        const auto first_keys = queue.get_first_x_span_keys(6);
        check(first_keys.size() == 6, "get_first_x_span_keys returns all 6 across DB+back page");
        check(first_keys[0] == keys[0].to_string(), "get_first_x_span_keys preserves FIFO order at index 0");
        check(first_keys[5] == keys[5].to_string(), "get_first_x_span_keys preserves FIFO order at index 5 (back page)");
    }

    // --- PendingQueue: push/pop, error routing, move back to pending ---
    {
        PendingQueue queue(dir, "pendingtest", /*page_size=*/100);
        const SpanKey key = SpanKey::generate();
        queue.push_pending(key, nlohmann::json{{"x", 1}}, 0);
        check(queue.get_pending_size() == 1, "push_pending increments pending size");

        auto popped = queue.pop();
        check(popped.has_value() && popped->data["x"] == 1, "pop() returns full PendingEntry with data intact");

        queue.push_error(key, nlohmann::json{{"x", 1}}, "simulated failure");
        check(queue.get_error_size() == 1, "push_error increments error size");
        check(queue.get_pending_size() == 0, "pending size back to 0 after error route");

        auto moved = queue.move_one_error_to_pending(key);
        check(moved.has_value() && (*moved)["x"] == 1, "move_one_error_to_pending returns the data");
        check(queue.get_pending_size() == 1 && queue.get_error_size() == 0, "entry actually moved queues");

        queue.shut_down();
    }

    std::printf("\nAll queue smoke tests passed.\n");
    return 0;
}
