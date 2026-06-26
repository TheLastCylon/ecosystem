#pragma once

#include <utility>

#include <asio/any_io_executor.hpp>
#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>

// Mirrors ekosis/util/fire_and_forget_tasks.py's fire_and_forget_task/run_soon.
// fire_and_forget_task_for_loop is NOT ported -- it has no real callers in
// ekosis either (only fire_and_forget_task does, from
// requests/buffered_handler_base.py).
//
// No task-tracking set here, unlike Python's module-level
// FIRE_AND_FORGET_TASKS: that set exists in Python specifically because an
// asyncio.Task with no remaining strong reference can be silently garbage-
// collected mid-flight -- a real correctness hazard. asio::co_spawn has no
// equivalent hazard: the executor itself keeps the spawned coroutine frame
// alive until it completes, so there's nothing to track.
//
// Needs an explicit executor, unlike Python's implicit
// asyncio.get_running_loop() -- asio has no ambient "current executor"
// concept at a plain synchronous call site (only inside an actual coroutine
// body, via co_await asio::this_coro::executor). ekocpp's handlers are
// plain functions today, not coroutines (see the project memory on this --
// it's a real, separately-tracked architectural gap), so there's no ambient
// executor to grab implicitly; it has to be threaded in, typically captured
// from ApplicationBase::io_context().get_executor() at registration time.

// Direct equivalent of fire_and_forget_task -- spawn an already-constructed
// awaitable, don't wait for it, return immediately.
template <typename Awaitable>
void fire_and_forget(asio::any_io_executor executor, Awaitable awaitable) {
    asio::co_spawn(executor, std::move(awaitable), asio::detached);
}

// Direct equivalent of the run_soon DECORATOR -- wraps a coroutine-returning
// callable so call sites look like an ordinary, immediately-returning
// function call:
//
//   auto log_request = make_fire_and_forget(executor, log_request_impl);
//   ...
//   log_request(span_key, data, timestamp); // returns immediately, runs independently
//
// log_request_impl itself stays a normal coroutine function
// (asio::awaitable<T>(...) signature) -- make_fire_and_forget only changes
// how its CALLER experiences calling it.
template <typename CoroutineFactory>
auto make_fire_and_forget(asio::any_io_executor executor, CoroutineFactory coroutine_factory) {
    return [executor, coroutine_factory](auto&&... args) {
        fire_and_forget(executor, coroutine_factory(std::forward<decltype(args)>(args)...));
    };
}
