#pragma once

#include "../data_transfer_objects/span_key.hpp"

// Per-thread chokepoint for the currently-active SpanKey. The C++ analogue
// of ekosis/requests/request_context.py's ContextVar -- but unlike a
// ContextVar, thread_local has no notion of "coroutine," only "thread."
//
// This is only correct because the vendored, patched asio
// (third_party/asio/include/asio/impl/awaitable.hpp's resume()) rewrites it
// on EVERY coroutine resume, not once per thread -- io_context runs many
// coroutines on one thread, interleaved at each co_await, so a bare
// thread_local would otherwise leak one coroutine's span_key into another's
// log lines. Read/write the ambient value from inside a coroutine via
// `co_await asio::this_coro::span_key` / `co_await
// asio::this_coro::set_span_key(key)` -- see documentation/
// ambient_span_context.md for the full design and why a standalone
// ekosis::awaitable<T> coroutine type (built, verified, then superseded
// same session) turned out not to be needed.
SpanKey& thread_local_span_key();
