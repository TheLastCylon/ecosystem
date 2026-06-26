#include <cstdio>
#include <string>
#include <vector>

#include <asio/io_context.hpp>

#include "../src/util/fire_and_forget.hpp"

namespace {

void check(bool condition, const char* what) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
    std::printf("ok: %s\n", what);
}

asio::awaitable<void> log_message(std::vector<std::string>& log, std::string message) {
    log.push_back(std::move(message));
    co_return;
}

} // namespace

int main() {
    asio::io_context io_context(1);
    std::vector<std::string> log;

    // --- fire_and_forget: spawning doesn't run the body immediately ---
    fire_and_forget(io_context.get_executor(), log_message(log, "first"));
    check(log.empty(), "fire_and_forget returns immediately -- the coroutine body hasn't run yet");

    io_context.run();
    check(log.size() == 1 && log[0] == "first", "the coroutine body actually ran once io_context.run() processed it");

    io_context.restart();

    // --- make_fire_and_forget: decorator-equivalent, plain-call-looking ergonomics ---
    auto log_it = make_fire_and_forget(io_context.get_executor(), [&log](std::string message) {
        return log_message(log, std::move(message));
    });

    log_it("second");
    log_it("third");
    check(log.size() == 1, "make_fire_and_forget's wrapper also returns immediately -- still just 'first' from before");

    io_context.run();
    check(log.size() == 3 && log[1] == "second" && log[2] == "third", "both fire-and-forget calls ran, in the order they were spawned");

    std::printf("\nAll fire_and_forget smoke tests passed.\n");
    return 0;
}
