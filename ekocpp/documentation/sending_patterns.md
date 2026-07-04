# Sending patterns -- the grid, and what v0.18.0 actually builds

This document exists because "add concurrency to `BufferedSender`" turned out
to expose a much bigger surface than one bug fix. Two independent axes
determine what a client actually needs to do, and crossing them produces a
combinatorial family of communication styles that no mainstream framework
tries to support in full -- most pick one point in the grid (typically 1:1
response pattern + persisted-or-per-call lifecycle) and stop there.
`BufferedSender` needs a point in the grid nothing we've built (or seen
elsewhere) covers by default. This doc names the whole grid so the scope of
v0.18.0 is a deliberate choice, not an oversight.

## Axis A -- response pattern

What shape is the relationship between sends and responses?

1. **1-send -> 1-response.** Today's default (`send_message`, Python's
   `sender` decorator). The overwhelming common case. Must stay simple and
   untouched -- every existing client already does this correctly.
2. **N-send -> N-response, handled individually as each arrives.**
   `BufferedSender`'s actual need: "make sure this is sent, retry if it
   isn't, I don't need anything else back beyond that." **This is the one
   pattern v0.18.0 builds.**
3. **N-send -> 1 aggregate response (scatter-gather / fan-in).** Wait for
   all N (or all that matter), combine into one result. Same underlying
   mechanism as #2, different completion policy layered on top.
4. **N-send -> first-response-wins (race).** Redundant sends to multiple
   destinations, take whichever answers first, discard the rest. Same
   mechanism again, different policy.
5. **N-send -> quorum-of-M.** Dynamo/Cassandra-style middle ground between
   #3 and #4.
6. **Send with no response at all.** True fire-and-forget, nothing ever
   comes back by protocol design (e.g. UDP telemetry). Genuinely simpler
   than #2 -- there's no demux problem if there's no reply to correlate.
7. **1-send -> N-response (inverted cardinality).** One request, a stream
   of replies over time until some terminator (subscription / paginated
   push / long-poll). The true architectural outlier -- needs its own
   frame-level thinking (a terminator flag), not just more `send_message`
   calls. Not investigated.

Patterns 3/4/5 are pattern 2's mechanism with different completion policies
on top. Pattern 6 is a genuinely different, simpler mechanism. Pattern 7 is
its own thing.

## Axis B -- connection lifecycle

How long does the underlying connection live, relative to the calls made
over it?

- **Per-call (Transient).** Fresh socket per call, zero shared state, dies
  immediately after. Already correct, already concurrency-safe by
  construction (nothing shared to contend over). Unchanged.
- **Always-open (Persisted).** One socket, held open indefinitely,
  heartbeat keeps it alive regardless of traffic. Today's `Persistent
  StreamClientBase`/`UDPClient`.
- **Open-while-busy, configurable idle-timeout.** Opens on first item to
  send, stays open while there's a backlog, closes after a configurable
  grace period of nothing pending. This is not a third client family
  sitting alongside the other two -- it's a generalisation that subsumes
  "Persisted" as its idle-timeout-is-infinite extreme, and gets close to
  "Transient" behaviour as idle-timeout approaches zero (with the caveat
  that it still holds state -- a reader loop, a demux map -- across more
  than one call, which pure Transient never does).

**Why this axis only applies to `SOCK_STREAM` transports (TCP, UDS):** the
whole reason a lifecycle axis exists is to decide when to pay (or avoid)
real connection-establishment cost -- a TCP/UDS handshake genuinely costs
something, and there's a genuine trade-off in amortising it (Persisted) vs.
not paying it when idle (burst). UDP has no handshake, no connection state,
nothing to amortise or avoid -- `connect()` on a UDP socket is a local
convenience, not a network event (confirmed by reading `udp_client.cpp`).
So "lifecycle" as a design question doesn't meaningfully exist for UDP at
all; see the UDP section below for why it drops out of this document's
scope entirely, not just this axis.

## The grid

This grid covers `SOCK_STREAM` transports (TCP, UDS) only. UDP is excluded
from the grid entirely -- see "UDP: excluded, not just deprioritised" below
for why it isn't a quieter cell but a structurally wrong fit for every
pattern here that isn't pure no-reply.

|                          | 1:1 (today) | N:N-individual | scatter/race/quorum | 1:N streaming |
|--------------------------|:-----------:|:---------------:|:--------------------:|:--------------:|
| Per-call (Transient)     | done, untouched | n/a -- nothing to multiplex over a socket that dies after one call | n/a | n/a |
| Always-open (Persisted)  | done, untouched | subsumed by burst-lifecycle row below (infinite timeout) | not needed yet | not investigated |
| Burst (configurable idle-timeout) | not needed -- burst lifecycle only matters when there's genuine concurrency to pipeline | **v0.18.0 builds this cell** | deferred | deferred |

The only cell anything currently needs is **N:N-individual x burst-lifecycle**.
That's `BufferedSender`'s exact contract: many independent sends in flight,
each handled on its own as it completes, over a connection that doesn't need
to exist when the buffer is empty.

## UDP: excluded, not just deprioritised

UDP does not appear anywhere in the grid above, and that's deliberate, not
an oversight. Two separate reasons, worth keeping distinct:

**1. The lifecycle axis (Axis B) doesn't apply to it.** UDP has no
handshake, no connection state, nothing to amortise -- there's no
lifecycle decision to make (see Axis B above).

**2. Multiplexing over UDP is a bad idea on its own terms, independent of
lifecycle.** UDP provides no ordering, no delivery guarantee, and -- the
one that actually matters here -- no congestion control. A `SOCK_STREAM`
transport throttles itself against a struggling receiver; UDP does not,
by design. Firing N requests concurrently at a receiver with no flow-control
signal means an overloaded server just silently drops what it can't keep
up with, which triggers retries, which adds more datagrams to an already
overwhelmed receiver -- a self-reinforcing failure mode, not a hypothetical
one (it's a real-world reason congestion control was invented for the
internet in the first place). Multiplexing doesn't introduce a *new*
correlation problem on top of UDP (the `SpanKey` demux needed for it would
actually fix a latent bug already present in today's single-in-flight
`UDPClient` -- a late response to a retried request can be misattributed
to the next request, since `send_once` just does a plain `async_receive`
with no correlation check). But it does turn "how much concurrency" into a
direct, unmediated knob on "how hard we hammer a receiver that cannot ask
us to slow down."

**Precedent worth naming plainly: this is exactly why RabbitMQ doesn't
support UDP.** Every protocol it speaks (AMQP, MQTT, STOMP) runs over TCP.
Its entire value proposition -- guaranteed, acknowledged, ordered delivery
-- would require reimplementing TCP's guarantees in userspace on top of a
transport actively fighting you, while simultaneously trying to uphold a
stronger promise on top of that shaky foundation. Nobody serious does that.
You inherit the guarantees you need from the transport layer built to
provide them, then add your own semantics on top.

**`BufferedSender`'s contract is the same shape as RabbitMQ's, just
smaller: retried, eventually-delivered, individually-acknowledged.** That
contract structurally requires a reliable, ordered transport underneath it.
UDP cannot provide that cheaply at any concurrency level -- 1:1 or
multiplexed makes no difference to this argument.

**Hard rule, stated plainly:**

> `BufferedSender` requires a client derived from `SOCK_STREAM` (TCP or
> UDS). Plain `UDPClient` is excluded today; a future
> `MultiplexedUDPClient`, should one ever be built, would be excluded too.
> This isn't a tuning recommendation -- it's a contract mismatch. If a
> caller genuinely wants pure fire-and-forget, no-correlation, no-retry
> UDP sends (pattern 6 above -- e.g. StatsD-style telemetry), that's a
> different, much simpler mechanism than `BufferedSender`, and a different
> conversation entirely.

**Enforcement:** excluded by construction, not by convention. See
"What v0.18.0 actually builds" below -- `MultiplexedStreamClientBase` only
ever parents `SOCK_STREAM`-backed clients, the same way `UDPClient` was
never under `StreamClientBase`/`PersistentStreamClientBase` today. UDP was
never eligible for "stream," multiplexed or not; nothing needs to remember
to reject it as a special case.

**QUIC, named and dismissed for a different reason, worth recording so it
isn't re-litigated:** QUIC rides on UDP but manufactures its own
TCP-grade ordering/reliability, so in principle it *could* someday satisfy
`BufferedSender`'s contract on its own terms. Not relevant now regardless:
QUIC's headline advantages (near-zero-RTT handshake resumption, connection
migration across changing IP addresses, multiplexing without head-of-line
blocking) solve problems specific to the open internet and mobile
browsers -- untrusted peers, roaming networks, large RTT to strangers.
None of that describes EcoSystem's actual deployment shape (LAN or
same-machine, trusted peers, UDS already winning on latency). If QUIC is
ever built, it's its own client, on its own day, evaluated on its own
merits -- not folded into this document's scope.

## What v0.18.0 actually builds

`Multiplexed{TCP,UDS}Client` -- one new class family, two concrete
types, both deriving from a new `MultiplexedStreamClientBase` (parallel to
how `PersistentTCPClient`/`PersistedUDSClient` both derive from
`PersistentStreamClientBase` today). No UDP variant -- see above.

Full design history and rationale -- lifecycle, the write-lock/reader-loop/
demux mechanism, reconnection ownership, heartbeat integration, per-request
timeout (reframed as operational visibility, not auto-heal), and why
`drain_concurrency` is still needed -- lives in `multiplexed_stream_client.md`.

- Opens its underlying socket lazily, on the first `send_message` call made
  while no connection exists.
- Write path: a lightweight write-lock serialises only the write itself
  (cheap), not the round trip.
- Read path: one background reader loop per open connection, demuxing each
  incoming frame to its caller via the `SpanKey` already present in every
  response header (`ParsedHeader.span_key`) -- a correlation ID that already
  exists on the wire today, currently used only for tracing.
- Idle-timeout: configurable, closes the underlying socket after N ms with
  nothing pending. Default TBD -- likely a short-but-nonzero grace period so
  a trickle of traffic doesn't thrash open/close, with 0 (strict
  close-on-empty) and infinite (behaves exactly like today's Persisted
  clients) both available as explicit opt-ins.
- Configuration surface mirrors `ConfigBufferedSender`'s existing pattern
  (env var + JSON key + sane default) -- not yet named.

`PersistentStreamClientBase` and `UDPClient` are **not modified**. Their
existing `send_permit_`-guards-the-whole-round-trip semantics stay exactly
as they are -- correct for 1:1, and every existing caller depends on that
semantics remaining unchanged. `BufferedSender` switches to holding a
`Multiplexed*Client` instead of a shared `Persisted*Client`; everything else
in the codebase is unaffected.

## Explicitly deferred, not forgotten

Every other cell in the grid: response patterns 3 through 7, and any
lifecycle/pattern combination beyond N:N-individual x burst. None of these
are ruled out -- they're simply not required by anything that exists today.
Should a future caller need scatter-gather, quorum, or true streaming, it
gets scoped and built against its own real need then, following the same
discipline this document follows now: name the need precisely, build only
that cell, defer the rest in writing.

## Open question, deliberately unresolved

Should a client's concurrency contract (1:1 vs. multiplexed) be explicit and
queryable on `ClientBase`, or stay implicit as it is today (buried inside
`.cpp` internals, discoverable only by reading source)? Most framework users
will only ever touch 1:1 clients and shouldn't carry conceptual weight for a
problem that is -- so far -- unique to `BufferedSender`. Left open until a
second caller of the multiplexed family exists and this stops being a
one-off.
