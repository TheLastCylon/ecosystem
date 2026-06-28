# Ambient span_key propagation -- vendored asio patch

**Status:** built, vendored, wired into the real connection handlers, and
verified live against `ekocpp_server` + `esnc`, 2026-06-23. SUPERSEDES an
earlier same-session attempt (a standalone `ekosis::awaitable<T>` coroutine
type) -- kept below for the record, since it's how the final design got
found, not because it's still relevant code.

## Problem

`ekosis`'s `request_context.py` gives any log call site ambient access to the
current `span_key` via a `ContextVar`, with zero `RequestContext` plumbing
required at the call site. `ekocpp` had no equivalent -- `thread_local` is
the obvious first reach, and it's wrong on its own: `io_context` runs many
coroutines on one thread, interleaved at every `co_await`, and a bare
`thread_local` has no notion of "coroutine," only "thread." Coroutine A can
suspend mid-request, coroutine B (a different connection, different
`span_key`) resumes on the same thread, and a log call inside A after it
wakes back up would silently read B's span_key with no error.

## First attempt: standalone ekosis::awaitable<T> (built, verified, then dropped)

A full standalone coroutine type with its own `promise_type`, using the
standard C++20 `await_transform` hook to rewrite `thread_local_span_key()` on
every resume. Built, and a real smoke test caught two genuine bugs in it
(documented in git history of this file) -- a naive "promise constructor
argument matching" seed mechanism that silently fell back to an all-zero
`SpanKey` if a handler's signature ever changed shape, and a nested-call
inheritance gap.

**Why it got dropped, not just superseded quietly:** wiring it into the real
`handle_stream_connection`/`handle_datagram` chokepoints required handing it
to `asio::co_spawn` -- which doesn't work. Confirmed empirically (not just
reasoned from docs): `asio::co_spawn`'s typed overloads only accept
`asio::awaitable<T, Executor>` (the `awaitable_signature` trait is only
specialized for that exact type), and an `asio::awaitable<void>` coroutine
cannot `co_await` an `ekosis::awaitable<T>` either -- asio's own promise
(`awaitable_frame_base<Executor>`) has a *closed* set of `await_transform`
overloads, each constrained to asio-internal types, with no generic
passthrough for externally-defined awaitable types. A real interop test
(`interop_check.cpp`) produced the actual compiler error: "no matching
function for call to `await_transform(ekosis::awaitable<int>)`."

Closing that gap would have meant building a parallel `ekosis::spawn()` with
its own detached-coroutine lifetime management -- effectively a second,
parallel coroutine *runtime*, not just a coroutine *type*. Recognized as
scope creep before being built: solving "ambient span_key for logging" by
constructing a second asio is a worse trade than the alternative below.

## Decision: vendor asio, patch awaitable_frame_base directly

Once `ekosis::awaitable<T>` was ruled out, the options were (a) build the
parallel runtime above, or (b) accept maintaining a vendored, patched copy of
asio. (b) was chosen deliberately -- "taking responsibility for doing this in
C++" rather than building around the problem.

**Why the patch is small, not a rewrite:** `asio::detail::awaitable_frame<T,
Executor>` -- confirmed via `std::coroutine_traits<asio::awaitable<T,
Executor>, Args...>` -- IS the `promise_type` for every `asio::awaitable<T,
Executor>`, for every `T`, with no exceptions. It derives from
`awaitable_frame_base<Executor>`, where `resume()` is the one function every
single resumption path (nested `awaitable<T>` calls, raw async ops,
everything) funnels through, and `push_frame()`/`pop_frame()` already
implement the exact parent/child call-stack discipline ambient propagation
needs. So the patch adds one field and two single-line edits to logic that
already exists, plus two new `await_transform` overloads following asio's
own `this_coro::executor_t` idiom exactly -- not new machinery.

## What's vendored and patched

`third_party/asio/include/` -- a full copy of system asio 1.28.1
(`/usr/include/asio.hpp` + `/usr/include/asio/`), used in place of the
`pkg_check_modules(ASIO REQUIRED asio)` system package.
`third_party/asio_patches/0001-ambient-span-key.patch` -- the actual diff
against pristine 1.28.1, kept under version control so re-applying against a
future asio upgrade is mechanical: a clean `patch` apply means nothing
relevant moved; a conflict says exactly what did.

**`asio/this_coro.hpp`** -- two new tag types, same shape as the existing
`executor_t`/`executor`:
- `span_key_t` / `constexpr span_key_t span_key;` -- read.
- `set_span_key_t` / `set_span_key(SpanKey)` -- write.

**`asio/impl/awaitable.hpp`** (`awaitable_frame_base<Executor>`):
- `SpanKey span_key{};` -- new member.
- `resume()` -- one new line, `thread_local_span_key() = span_key;` before
  `coro_.resume();`. The single chokepoint every resumption path shares.
- `push_frame(caller)` -- one new line, `span_key = caller_->span_key;`.
  Nested `co_await` of another `asio::awaitable<T>` inherits the caller's
  ambient `span_key` automatically, no parameter needed for that purpose.
- `await_transform(this_coro::span_key_t)` -- returns the current frame's
  `span_key`, mirrors `await_transform(this_coro::executor_t)` exactly (no
  real suspension, `await_ready()` returns `true`).
- `await_transform(this_coro::set_span_key_t)` -- writes `span_key` on the
  frame AND `thread_local_span_key()` immediately (so it's correct even
  before this coroutine's own next `resume()`).

Both new files reach into `ekocpp`'s own `src/` via relative include
(`../../../../src/data_transfer_objects/span_key.hpp` from `this_coro.hpp`,
one level deeper from `impl/awaitable.hpp`) -- a deliberate, documented
coupling. This vendored copy is `ekocpp`'s own fork, not a drop-in
replacement for anyone else's vanilla asio.

## Wired into real handlers

`src/servers/stream_server_base.cpp` (`handle_stream_connection`, the
per-connection loop shared by TCP/UDS) and `src/servers/udp_server.cpp`
(`handle_datagram`, spawned fresh per datagram) both call
`co_await asio::this_coro::set_span_key(parsed.span_key);` immediately after
`parse_header` -- the actual C++ analogue of `_route_request`'s
`_set_current_span_key()` call.

## Verified live

Real `ekocpp_server` + real `esnc` traffic (not a synthetic test): three
separate TCP connections, three distinct `span_key`s, `echo_handler`
temporarily instrumented to print `thread_local_span_key()` alongside the
explicitly-passed `span_key` -- all three connections showed `match=YES`.
Diagnostic reverted after confirming.

Also verified against real asio mechanics in isolation (`asio_patch_check.cpp`,
real `asio::post` suspension, real `io_context::run()`, real `co_spawn`):
`thread_local_span_key()` survives being deliberately clobbered across a real
suspend/resume cycle; a per-loop-iteration `set_span_key` survives a
subsequent suspension; a nested `co_await` of a second coroutine inherits the
caller's `span_key` with nothing passed for that purpose.

## NEXT

- `ekosis::awaitable<T>` and its smoke test were deleted, not kept around
  unused -- `src/coroutines/awaitable.hpp` no longer exists.
  `ambient_span_context.{hpp,cpp}` kept (`thread_local_span_key()` is still
  the actual storage the patch writes into).
- Re-applying `0001-ambient-span-key.patch` on a future asio version bump is
  untested -- the patch is new as of tonight, no upgrade has happened yet.
- The child-span scenario (a user wanting a nested span_id under the same
  trace_id for a sub-operation, then reverting after) is still open --
  flagged during this same session, not solved. `push_frame`'s inheritance
  gives a starting point (the same save/restore-on-frame-boundary shape), but
  needs its own design pass.
