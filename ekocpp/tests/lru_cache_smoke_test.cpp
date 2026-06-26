#include <cstdio>
#include <string>

#include "../src/cacheing/lru_cache.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

} // namespace

int main() {
    LRUCache<std::string, int> cache(10);

    // --- basic set/get ---
    check(cache.size() == 0, "starts empty");
    cache.set("0", 0);
    check(cache.get("0") == 0, "get() returns the value just set");
    check(cache.size() == 1, "size() == 1 after one set");

    // --- pop_item ---
    check(cache.pop_item("0") == 0, "pop_item('0') returns 0");
    check(cache.size() == 0, "size() == 0 after pop_item drains the only entry");
    check(!cache.pop_item("does_not_exist").has_value(), "pop_item on missing key returns nullopt");

    // --- fill to capacity (10) ---
    for (int i = 0; i < 10; ++i) cache.set(std::to_string(i), i);
    check(cache.size() == 10, "size() == 10 after filling to capacity");
    for (const auto& k : cache.keys()) {
        check(std::stoi(k) == *cache.peek(k), ("filled value matches its key for " + k).c_str());
    }

    // --- overfill: 10 more keys evict the original 10 ---
    for (int i = 10; i < 20; ++i) cache.set(std::to_string(i), i - 10);
    check(cache.size() == 10, "size() stays at capacity (10) after overfilling");
    {
        int count = 0;
        for (const auto& k : cache.keys()) {
            count++;
            check(std::stoi(k) - 10 == *cache.peek(k), ("evicted-and-refilled value matches for key " + k).c_str());
        }
        check(count == 10, "exactly 10 keys remain after overfilling");
    }

    // --- peek vs get (peek must not alter cache order; pop() proves it below) ---
    check(*cache.peek("10") == 0, "peek('10') == 0");
    check(!cache.peek("does_not_exist").has_value(), "peek on missing key returns nullopt");
    check(*cache.get("10") == 0, "get('10') == 0");
    check(*cache.get("19") == 9, "get('19') == 9");
    check(!cache.get("does_not_exist").has_value(), "get on missing key returns nullopt");

    // --- pop() removes the MOST-recently-used entry (front), not the LRU one ---
    // '19' was the last successful set() in the overfill loop, and the get('19')
    // just above re-promoted it to front -- so it must be what pop() returns.
    {
        auto popped = cache.pop();
        check(popped.has_value() && popped->first == "19" && popped->second == 9,
              "pop() removes the most-recently-used entry ('19'), not an LRU one");
        check(cache.size() == 9, "size() == 9 after pop()");
    }

    // --- contains / erase ---
    check(cache.contains("10"), "contains('10')");
    check(!cache.contains("0"), "'0' was evicted by overfilling, contains('0') is false");
    cache.erase("18");
    check(!cache.contains("18"), "erase('18') removes it");
    check(cache.size() == 8, "size() == 8 after erase");

    // --- re-set an existing key updates value without growing size ---
    check(*cache.peek("17") == 7, "peek('17') == 7 before update");
    cache.set("17", 14);
    check(*cache.peek("17") == 14, "peek('17') == 14 after re-set");
    check(cache.size() == 8, "size() unchanged by updating an existing key");

    // --- clear ---
    cache.clear();
    check(cache.size() == 0, "size() == 0 after clear()");
    check(!cache.pop().has_value(), "pop() on an empty cache returns nullopt");

    std::printf("\nAll LRU cache smoke tests passed.\n");
    return 0;
}
