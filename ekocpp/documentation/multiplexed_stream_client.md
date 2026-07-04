# MultiplexedStreamClientBase -- design history and rationale

This document captures the full reasoning behind `MultiplexedStreamClientBase`,
the class family `BufferedSender` will hold instead of a shared
`Persisted*Client`. See `sending_patterns.md` for the grid this cell sits in
and why UDP is excluded entirely. This doc is the "how and why" for the one
cell that document says v0.18.0 actually builds.

## Why a new class, not a modified PersistentStreamClientBase/UDPClient

The original 2026-07-02 direction was to patch pipelining into the internals
of `PersistentStreamClientBase` and `UDPClient` directly (permit-guards-write
instead of permit-guards-round-trip). Walked back: that changes semantics
every existing caller of those classes already depends on, for the benefit
of one caller (`BufferedSender`). A separate class family isolates all new
complexity (write-lock, reader loop, demux map) to only the code that opts
into it -- the existing blocking clients stay exactly as they are, untouched,
still simple, still correct.

## Lifecycle: always-open, no idle-timeout

An earlier version of this design added a configurable idle-timeout
(open-while-busy, close after a grace period of nothing pending), reasoning
that holding a connection open for nothing seemed wasteful. Walked back after
checking it against real precedent: RabbitMQ (AMQP explicitly discourages
connection-per-operation), Kafka, gRPC/HTTP2, and Redis (whose pipelining
model doesn't even use correlation IDs -- it relies on strict same-connection
response ordering) all default to holding one persistent connection per known
peer open indefinitely. The systems that *do* close idle connections (HTTP/1.1
keep-alive, DB connection pools) are solving a different problem -- an
unbounded or scarce-resource set of *many possible peers* -- not "this one
fixed, known downstream service is occasionally idle." `BufferedSender` talks
to one fixed peer, known in advance. That's exactly the shape where nobody in
the wild bothers closing on idle, and the connection-establishment tax is
real enough that reopening it for no demonstrated benefit is pure waste.

**Conclusion: `MultiplexedStreamClientBase` is always-open, full stop.** No
idle-timeout parameter, no open/close state machine to build or test. It
inherits `PersistentStreamClientBase`'s existing lifecycle model (connect
once, heartbeat, stay open) and changes only what happens on top of that
connection.

## The mechanism: write-lock + reader loop + SpanKey demux

- **Write path:** a lightweight write-lock serialises only the write itself
  (cheap), not the round trip. N callers can each fire a request without
  blocking on each other or on any response.
- **Reader loop:** one background coroutine, the sole reader of the socket,
  demuxing each incoming frame to its caller via the `SpanKey` already
  present in every response header (`ParsedHeader.span_key`) -- a
  correlation ID that already exists on the wire today, currently used only
  for tracing.
- **Demux map:** `SpanKey -> completion channel`, protected by a mutex (not
  the write-lock -- reader and writers both touch the map independently of
  the write path). A caller registers its own completion channel under its
  `SpanKey` before writing; the reader loop looks up the matching entry when
  a frame arrives and delivers via `try_send` (never blocks the reader loop
  waiting on a slow/abandoned caller). A response with no matching entry
  (already timed out, or a stray/duplicate) is silently discarded as an
  orphan.

A caller's experience is unchanged from today's `send_message` ergonomic --
still "await my response" -- but underneath, many of those awaits are now
genuinely concurrent against one shared socket instead of serialized behind
a single permit.

## Reconnection: ensure_connected() owns it, same as today

Correction made mid-design: the heartbeat does not itself "own"
reconnection. `ensure_connected()` does -- called by both the heartbeat loop
and the send path, whichever notices `connected_ == false` first. The
heartbeat's actual job (per its existing docstring) is narrower: detect a
stale connection *during idle gaps*, when nothing else would notice.

**Heartbeat is negated by real traffic.** If sends are flowing, every
successful send already proves the connection is alive -- a heartbeat ping
in that window is pure redundant cost. Fix: reset the heartbeat timer's
expiry on every successful send. The heartbeat only fires if the timer
expires *without* being reset by real traffic in the interim -- exactly
matching its actual purpose. (Deliberately not backported to
`PersistentStreamClientBase` -- that class stays untouched, per the
no-modification decision above.)

**Heartbeat must ride the same demux -- not optional, forced by
correctness.** Once the reader loop is the sole reader of the socket,
`do_heartbeat()` cannot also perform its own independent `async_read` on
that socket -- two coroutines reading the same socket concurrently race,
whichever is scheduled first steals bytes meant for the other, corrupting
framing for both. So `do_heartbeat()` packs its ping, registers the ping's
`SpanKey` in the demux map, and awaits its own completion channel exactly
like any other caller. This also simplifies `do_heartbeat()` versus today's
version, which needed its own read-with-timeout-race logic.

**Reader loop lifecycle: spawned fresh per connection, not one long-lived
loop surviving reconnects.** Rather than inventing a wake-up mechanism for a
dormant reader loop when a new connection replaces a dead one,
`ensure_connected()` spawns a new reader-loop coroutine tied to the specific
socket it just opened, each time it reconnects. Simpler than trying to keep
one reader loop alive across a socket's death and replacement.

## Connection death mid-flight: fail everyone, resend, duplication is a
server-side concern

When the reader loop hits a read error, it walks the demux map and fails
every outstanding entry at once (not just one caller), then marks
`connected_ = false`. Each caller's own `send_message_retry_loop` -- unchanged
from today's per-call logic -- takes it from there independently: catches
the failure, retries, calls `ensure_connected()` (reconnects once, spawns a
fresh reader loop), re-sends. No new batch-retry logic needed anywhere; it's
the existing per-call retry mechanism, just now N independent instances of
it instead of one.

**Duplication on retry is possible, and it is not the client's problem to
solve.** A client that can't tell whether the server processed a request
before the connection died has exactly one honest option -- retry -- and no
way to make that retry safe without server-side cooperation. This is the
standard at-least-once delivery problem; real systems (Stripe's API is the
canonical example) solve it with idempotency keys on the *server* side, not
client-side cleverness. `SpanKey` is already on every request today --
if idempotent-handler support is ever wanted, the plumbing to dedupe against
it costs nothing new to add later. Not built now. This risk is not new to
multiplexing either -- it already exists in `BufferedSender`'s
retry-on-`CommunicationsMaxRetriesReached` contract today, one request at a
time; multiplexing just means N requests can fail together instead of one.

## Per-request timeout: reframed as operational visibility, not auto-heal

Initial design assumed a per-request timeout that would fire a retry, mirroring
today's blocking-read-with-timeout pattern. Re-examined from why timeout
existed at all in the old model: in a blocking, single-in-flight client,
timeout was the *only* way to escape a permanent hang. Two things changed:

1. Multiplexing means a slow request no longer blocks anything else --
   nothing is waiting behind it, so "give up early" has lost its urgency.
2. Connection death is already a separate, solved problem (the reader
   loop's fail-everyone-on-read-error mechanism above) -- a per-request
   timer doesn't need to also cover "is the connection dead."

What's genuinely left: the connection stays healthy (heartbeat keeps
succeeding), but the server has a bug or edge case where it silently never
responds to one specific request while everything else on that connection
keeps working. That's not a connection failure and not ordinary slowness --
it's a stuck, permanently-unanswered demux-map entry, a real (if slow)
resource leak.

**Decision: do not auto-retry on this. Surface it, don't heal it.** This is
explicitly "a developer needs to look at this, we genuinely don't know what
the right recovery is" territory, not something the client should silently
paper over.

**Mechanism: a periodic sweep, not a per-request timer.** Structurally
similar to the heartbeat loop -- wakes on an interval, walks the demux map
under its mutex, checks each entry's registration timestamp against a
configurable staleness threshold, logs a warning once per entry that
crosses it (flagged so it doesn't repeat every sweep). Nothing is removed
from the map, nothing is retried, no exception is thrown. This also sidesteps
the `SpanKey`-reuse race a per-request-timeout-that-tears-down-the-connection
approach would have needed to solve (see "rejected: timeout tears down the
connection" below) -- since nothing is ever removed or re-registered, there's
no window for a late response to be misattributed to a different attempt.

**Accepted, named cost: this leaks more than memory.** Since nothing
auto-heals, the *caller's own coroutine* stays parked on its completion
channel forever too. For `BufferedSender`, that means one of its
`drain_concurrency` slots is gone for good, silently, each time this fires --
a slow leak in effective concurrency, not just memory, over a long-running
process. Accepted as a rare, exceptional-case cost given how infrequently
this should ever actually fire; revisit only if real operational data shows
otherwise.

**Rejected alternative: per-request timeout that tears down the
connection on fire, to unify with the hard-failure path.** Considered
during design: making a timeout behave exactly like a hard disconnect
(mark `connected_ = false`, force every retry onto a fresh connection) would
have cleanly eliminated a narrow race -- a merely-slow (not dead) response to
an earlier attempt arriving after a same-`SpanKey` retry has re-registered on
the same still-live connection, and being misattributed to the retry.
Superseded by the operational-visibility reframe above: once timeout no
longer triggers a retry at all, this race can't occur, so the rejected fix
is moot. Recorded here so it isn't re-derived and re-solved from scratch
later.

## drain_concurrency: still needed, not redundant

Checked directly: does multiplexing make `BufferedSender`'s
`drain_concurrency` unnecessary? No -- multiplexing and `drain_concurrency`
solve two different halves of the same problem. Multiplexing makes the
*client* capable of serving N requests at once; something still has to
actually *ask* for N at once for that capability to be used. A single drain
loop that does `pop() -> co_await send_message() -> pop() -> ...` only ever
has one request in flight, no matter how capable the client underneath it
is -- the loop's own coroutine suspends at the `co_await` and doesn't pop the
next item until its own response returns.

`drain_concurrency` is what actually turns "the client can do N at once"
into "N things are happening at once": N separate coroutines, each
independently popping and awaiting, running concurrently against the same
shared multiplexed connection. This was the original intent from the
2026-06-30/07-02 sessions, before the send_permit_ bug was found -- "once
the client pipelines, `drain_concurrency=8` becomes exactly the thing that
puts 8 requests in flight at once." Today's work is what finally makes that
true.

Considered and rejected: restructuring the drain loop to fire-and-continue
(spawn a detached task per popped item instead of awaiting inline) would get
concurrency without a `drain_concurrency` count at all -- but with no cap
whatsoever, fanning out as fast as the queue allows. Given real, bounded
resource cost still exists even over a flow-controlled TCP/UDS connection
(memory for buffered items, thread-pool pressure), an explicit, deliberate
cap is the right call over an uncapped fan-out.

## Incident: two BufferedSenders must never share one MultiplexedClient

Found live, in `observable_fun`'s router, the first time this code ran
against real traffic rather than a smoke test -- exactly the kind of gap
"verify against a live server, not just compile clean" exists to catch.

**Symptom:** `app.log_response` drained normally. `app.log_request` did not
drain at all.

**Root cause:** `router/main.cpp`'s `process_message` deliberately enqueues
both the request log and the response log using the *same* `span_key` --
the originating request's, not a fresh one:

```cpp
log_request_sender_->enqueue(TrackerLogRequestDto{dto.request, unix_now()}, span_key);
// ... downstream call happens here ...
log_response_sender_->enqueue(TrackerLogRequestDto{response, unix_now()}, span_key);
```

This is deliberate, not a mistake -- it's what makes tracker's log entries
show up correlated with the original request's trace in Jaeger (the
project's existing "one UUID, full distributed trace" pattern). It was
harmless before today, because `tracker_client_` was a single
`PersistedUDSClient` serialising everything to one request at a time --
there was never a second concurrent send for the same key to collide with.

Both `log_request_sender_` and `log_response_sender_` shared **one**
`MultiplexedUDSClient` (`tracker_client_`). A multiplexed client's demux map
is keyed by `SpanKey` -- and it must be unique per request *actually in
flight*, which the router's deliberate key-reuse violates the moment there's
real concurrency to exploit. Whichever of the two sends registers second in
the shared `unordered_map<SpanKey, DemuxEntry>` silently **overwrites** the
first entry -- no exception, no log line, just gone. Since `log_response`'s
enqueue always happens chronologically after `log_request`'s in
`process_message` (the response isn't known until processing finishes),
`log_response`'s registration reliably won the overwrite race before
`log_request`'s actual response could arrive. `log_request`'s
`send_message_retry_loop` was left registered nowhere, awaiting a channel
that would never be signalled -- and since ordinary sends deliberately carry
no per-request timeout (see above), nothing ever rescued it. Enough of these
and every one of `log_request_sender_`'s `drain_concurrency` slots ends up
permanently parked -- which is exactly "not draining at all."

**The deeper fact this exposes:** the wire's `SpanKey` field has always
served exactly one job -- tracing correlation -- until this session also
repurposed it as the client's own demux correlation key. Those two jobs want
opposite things: tracing wants deliberate reuse across related sends; demux
requires strict uniqueness per request in flight on a given connection.
Serialization used to hide the conflict; multiplexing exposes it the moment
two senders share a client.

**Fix applied:** give `log_request_sender_` and `log_response_sender_` their
own, separate `MultiplexedUDSClient` instances. Separate instances mean
separate demux maps -- the identical `span_key` literal value can be reused
by both forever and never collide, because collision requires *sharing the
map*, not merely sharing the value. Tracing correlation is fully preserved;
nothing about that behaviour changed. Verified live against the running
stack: both senders drain correctly.

## BufferedSender owns its client -- register_buffered_sender takes
connection parameters, not a client

The incident above is a direct, structural consequence of a design choice:
`register_buffered_sender` used to accept a caller-constructed
`shared_ptr<ClientT>`, which is exactly the shape that let one client get
handed to two different senders in the first place. The `MultiplexedClient`
concept constraint (excluding UDP) caught the *wrong type* of client; it was
never going to catch the *same* client used twice, because that's not a
type problem, it's an aliasing problem, and no type-level concept can see
that two `shared_ptr`s happen to point at one object.

**Decided: remove the shape that makes the mistake possible, rather than
add a check that detects it after the fact.** Two weaker options were
considered and rejected first:
- **A runtime "already claimed" flag on the client**, checked at
  registration. Rejected -- fires only after the mistake is already made,
  same category as a lint rule bolted on top rather than a structural
  guarantee.
- **Move-only handoff** (`unique_ptr` at the API boundary, promoted to
  `shared_ptr` internally). Rejected as insufficient on its own -- it stops
  a caller handing over the *same* `shared_ptr` twice, but nothing stops
  sloppier code further upstream from ending up in the same place by a
  different route.

**What was built instead:** `ApplicationBase::register_buffered_sender` no
longer accepts a client at all. It takes connection parameters -- a socket
path (UDS overload) or a host+port (TCP overload) -- and constructs a fresh
`MultiplexedUDSClient`/`MultiplexedTCPClient` internally on every call,
calling `->start()` itself. An application author registering two senders
against the same downstream service now gets two independent clients by
construction, every time, with no way to express sharing one even if they
wanted to.

**`BufferedSender`'s own constructor still accepts an explicit client**,
still gated by the `MultiplexedClient` concept -- this was deliberately
kept, not an oversight. Direct construction of `BufferedSender` was never a
supported application-facing pattern (only `register_buffered_sender` is);
the client-accepting constructor exists as a lower-level seam so unit tests
(`buffered_sender_smoke_test.cpp`'s `FakeClient`,
`standard_endpoints_buffered_management_live_test.cpp`'s `AlwaysFailClient`)
can inject controlled failure behaviour without a real socket. Those two
test doubles opt into `MultiplexedClient` via the explicit
`is_reliable_transport_test_double` marker described above -- not by
inheriting real transport machinery they have no need for.

**Visibility split, worth remembering:** the shared registration tail
(queue setup, statistics registration, shutdown wiring) lives in
`ApplicationBase::register_buffered_sender_with_client`, marked `protected`,
not `private`. A subclass (a test app) can still reach it directly to
register a sender with an explicit client -- that's a deliberate,
subclass-authored escape hatch. It's a different thing entirely from the
old public overload, which let *any* external caller holding an
`ApplicationBase&` pass in *any* client, shared or not.

## Future work, explicitly deferred: drain_concurrency vs. per-request latency

Not a v0.18.0 concern -- named here so it isn't lost. `BufferedSender`'s
real throughput ceiling isn't request rate in the abstract, it's
`drain_concurrency` divided by average per-request latency to the
downstream service. Tracker's local SQLite writes are fast, so 8 concurrent
slots go a long way (observed live: ~7k requests/minute sustained drain,
comfortably above the project's own "100 req/min is petty-cash
infrastructure" bar, even though it's well under the raw multiplexed
client's demonstrated ceiling of 3.4k+ req/s in isolation -- something else,
likely the on-disk `PendingQueue` write per `enqueue()` call or tracker's
own upsert-pattern DB writes, is the actual limiting factor now, not the
client built this session). A genuinely slower (high-latency, not
overloaded) downstream would hit a real ceiling at a much lower request
rate purely from slots × latency -- `drain_concurrency` is the dial to
reach for if that ever matters. Flagged as relevant future work for
Enounce specifically (fan-out to many subscribers is a different traffic
shape than anything `observable_fun` exercises), not investigated further
now.

## What still needs deciding before implementation

- Staleness-sweep interval and warning threshold -- both should be
  configurable, following `ConfigBufferedSender`'s existing pattern (env
  var + JSON key + sane default), defaults not yet chosen. **Still open** --
  current implementation hardcodes 30s sweep / 60s warning threshold as
  constructor defaults; no env/JSON wiring yet.
- ~~Exact completion-channel type/shape for the demux map value~~ --
  resolved: `concurrent_channel<void(error_code, vector<uint8_t>)>`, a set
  `error_code` is thrown as `std::system_error` by `use_awaitable`
  automatically, not returned as part of a tuple.
- Whether `MultiplexedTCPClient`/`MultiplexedUDSClient` need their own
  `ConfigMultiplexedClient`-style struct, or reuse existing timeout/
  heartbeat-period constructor parameters unchanged from
  `PersistentStreamClientBase`'s shape. **Still open** -- current
  implementation reuses the existing constructor-parameter shape, no config
  struct built yet.

## What does NOT change

`PersistentStreamClientBase` and `UDPClient` are not modified in any way --
every existing caller's semantics remain exactly as they are today.
`BufferedSender` switches to holding a `Multiplexed*Client` instead of a
shared `Persisted*Client`; everything else in the codebase is unaffected.
