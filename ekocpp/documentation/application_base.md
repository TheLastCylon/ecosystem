# ApplicationBase -- vision, not yet built

**Status:** forward-looking note, 2026-06-21. Nothing in this file is implemented.
`ekocpp` today is `main.cpp` constructing a `RequestRouter` and an `asio::io_context`
directly, by hand. This document captures where that's headed, so the shape isn't lost
before the next session picks it up.

## The target shape

`ekocpp` becomes a library (already split out as `ekocpp_lib` in `CMakeLists.txt` --
this was the right call early, it pays off here). A user links against it, derives
their own application class from `ApplicationBase`, registers their endpoints, and runs
one instance of their derived class. `main()` in user code becomes small:

```cpp
class MyApp : public ApplicationBase {
public:
    MyApp() {
        register_endpoint("echo", echo_handler);
    }
};

int main() {
    MyApp app;
    app.start();
}
```

This is deliberately the same shape as Python `ekosis`'s `ApplicationBase`
(`ekosis/application_base.py`) -- a user app subclasses it, gets a request router,
multi-transport servers (TCP/UDP/UDS), a statistics keeper, signal handling, and a
start/stop lifecycle for free. The C++ side should follow that structure closely where
the underlying need is identical, and diverge only where C++ idioms genuinely demand it.

## Where the two should match (same need, same answer)

- **Multi-transport servers** -- TCP/UDP/UDS, each optional based on configuration,
  each with its own start/stop. `ekocpp`'s `asio` equivalents are direct: an
  `asio::ip::tcp::acceptor`-backed listener, a UDP socket reader, a UDS acceptor --
  all three already proven shapes from `ekosis_net_cat`'s client side, just inverted
  to the server role.
- **Signal handling for graceful shutdown** -- Python wires `SIGTERM`/`SIGINT`/`SIGHUP`
  to raise `TerminationSignalException`, caught by `__exit__`. `asio::signal_set`
  is the direct equivalent -- register the same three signals, on catch, stop the
  `io_context` (which unwinds every pending coroutine cleanly via cancellation).
- **Singleton instance + lock file check** -- one running instance per
  `(application_name, instance_id)`, enforced via a lock file holding the process id,
  checked with `kill(pid, 0)` (Python) / `kill(pid, 0)` is POSIX either way -- this one
  ports near-verbatim, no language-specific complication.
- **`setup_tasks()` as a user-overridable hook** -- Python's `ApplicationBase` has
  `async def setup_tasks(self, tasks: list): pass`, overridden by user apps that need
  extra background work alongside the servers. C++ equivalent: a virtual method
  `setup_tasks()` that derived classes override, called from `start()` before
  `io_context.run()`, where the user can `co_spawn` whatever extra coroutines they need.
- **Buffered handlers / buffered senders lifecycle** -- `setup()`/`shut_down()`/
  `wait_for_shutdown()` per buffered handler and sender, gathered alongside the server
  tasks. Not built in C++ yet at all (no queue exists yet -- see `tier1_state.md`
  NEXT item), but the lifecycle shape to aim for once it exists.
- **Statistics keeper** -- periodic stats gathering task, same shape, ported once
  there's a reason to (not urgent for `ekocpp`'s current scope).

## Where the two should diverge (different language, different right answer)

- **Endpoint registration: explicit call, not a decorator.** Already decided this
  session (see the `function_traits`/static-registration discussion) -- Python's
  `@endpoint("echo")` works because import-time execution gives a free, ordered hook
  to run registration code. C++ has no equivalent guarantee across translation units
  (the "static initialization order fiasco" risk, discussed and explicitly rejected
  this session). So: `register_endpoint("echo", echo_handler)` called explicitly,
  inside the derived class's constructor (or an `setup_endpoints()` override, naming
  not yet decided) -- visible, ordered, no hidden global state. This is the one
  deliberate structural difference from Python, not an oversight.
- **Singleton via metaclass vs explicit construction.** Python's `ApplicationBase`
  uses `metaclass=SingletonType` -- instantiate it anywhere, always get the same
  object. C++ has no metaclass mechanism; the natural equivalent is the derived class
  itself simply being the one object constructed in `main()`, with `ApplicationBase`
  holding non-static members instead of Python's class-level singleton state.
  Simpler in C++, not a loss -- Python needed the singleton trick partly to let
  free-function endpoint handlers (registered at import time, before any
  `ApplicationBase` instance necessarily exists yet) reach the router; C++'s explicit
  construction order makes that unnecessary.
- **`async with` context manager vs RAII.** Python's `__enter__`/`__exit__` pairs
  setup/signal-handling with guaranteed shutdown-on-exception. C++'s direct
  equivalent is RAII -- a guard object whose destructor does the
  `__do_shutdown()`-equivalent work, so it runs on any exit path (normal return,
  exception, `io_context::stop()`) without an explicit `try`/`catch` at every call
  site. More idiomatic than trying to imitate `__enter__`/`__exit__` literally.

## NEXT

Not scoped yet -- this file exists so the shape survives to next session, not as a
commitment to build it immediately. The queue/buffered-handler work (already flagged
as NEXT in `tier1_state.md`) likely comes first, since `ApplicationBase`'s buffered
handler lifecycle has nothing to manage until that exists.
