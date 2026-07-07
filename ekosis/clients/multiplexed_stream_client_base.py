import time
import asyncio
import logging

from abc import ABC, abstractmethod
from typing import Dict, Tuple

from .client_base import ClientBase

from ..data_transfer_objects import HEADER_LENGTH, PING_FLAG, SpanKey, parse_header, pack_ping_frame

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
)

log = logging.getLogger()


# --------------------------------------------------------------------------------
# One demux-map entry per request currently in flight. `future` is a single-use
# completion signal (asyncio's natural equivalent of ekocpp's single-slot
# concurrent_channel) -- the reader loop resolves it with the response frame,
# or fail_all_outstanding resolves it with an exception if the connection dies
# first. `warned` mirrors ekocpp's DemuxEntry: the staleness sweep logs once
# per entry, not every sweep.
class _DemuxEntry:
    __slots__ = ("future", "registered_at", "warned")

    def __init__(self, future: asyncio.Future):
        self.future       : asyncio.Future = future
        self.registered_at: float           = time.monotonic()
        self.warned       : bool            = False


# --------------------------------------------------------------------------------
# Python port of ekocpp's MultiplexedStreamClientBase -- full design history and
# rationale in ekocpp/documentation/multiplexed_stream_client.md. One connection,
# held open indefinitely (see that doc's "Lifecycle" section), but unlike
# PersistentStreamClientBase, many send_message() calls can be genuinely in
# flight at once: a write lock serialises only the write itself, and a
# background reader loop demuxes each incoming frame to its caller via the
# SpanKey already present in every response header.
#
# No explicit mutex around __demux_map -- unlike ekocpp, which genuinely runs
# the reader loop and writers across a thread pool, Python's asyncio is single-
# threaded and cooperative: dict mutations here are plain, non-await
# statements, so there's no interleaving window for a race the way there would
# be across real OS threads.
class MultiplexedStreamClientBase(ClientBase, ABC):
    def __init__(
        self,
        timeout                    : float = 5,
        heartbeat_period           : float = 60,
        max_retries                : int   = 3,
        retry_delay                : float = 0.1,
        staleness_sweep_period     : float = 30,
        staleness_warning_threshold: float = 60,
    ):
        super().__init__(max_retries, retry_delay)
        self.__timeout                    : float                     = timeout
        self.__heartbeat_period           : float                     = heartbeat_period
        self.__staleness_sweep_period      : float                     = staleness_sweep_period
        self.__staleness_warning_threshold : float                     = staleness_warning_threshold
        self.__connected                  : bool                      = False
        self.__stopping                   : bool                      = False
        self.__reader                     : asyncio.StreamReader      = None
        self.__writer                     : asyncio.StreamWriter      = None
        self.__write_lock                 : asyncio.Lock              = asyncio.Lock()
        self.__connect_lock               : asyncio.Lock              = asyncio.Lock()
        self.__demux_map                  : Dict[SpanKey, _DemuxEntry] = {}
        self.__reader_task                : asyncio.Task              = None
        self.__heartbeat_task             : asyncio.Task              = None
        self.__staleness_sweep_task       : asyncio.Task              = None

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]: # pragma: no cover
        pass

    # --------------------------------------------------------------------------------
    # Call once, after construction, to start the background heartbeat and
    # staleness-sweep loops. No shared_from_this() equivalent concern in
    # Python, but kept as an explicit call (not constructor-implicit) to mirror
    # ekocpp's lifecycle discipline -- callers of MultiplexedTCPClient/
    # MultiplexedUDSClient should start() and stop() them explicitly.
    def start(self):
        loop                         = asyncio.get_event_loop()
        self.__heartbeat_task       = loop.create_task(self.__run_heartbeat_loop())
        self.__staleness_sweep_task = loop.create_task(self.__run_staleness_sweep_loop())

    # --------------------------------------------------------------------------------
    # Await before releasing the last reference to this client, to confirm both
    # background loops (and the reader loop, if a connection is open) have
    # actually exited before teardown.
    async def stop(self):
        self.__stopping = True
        tasks = [t for t in (self.__heartbeat_task, self.__staleness_sweep_task, self.__reader_task) if t is not None]
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

    # --------------------------------------------------------------------------------
    # Guarded by __connect_lock -- NOT redundant with __write_lock. __write_lock
    # guards only the write itself, so multiple callers can race into
    # ensure_connected() concurrently on a fresh disconnect. Without its own
    # guard, that race can open two connections and spawn two reader loops for
    # what should be one. See multiplexed_stream_client.md.
    async def __ensure_connected(self):
        async with self.__connect_lock:
            if not self.__connected:
                self.__reader, self.__writer = await self.open_connection()
                self.__connected             = True
                self.__reader_task           = asyncio.get_event_loop().create_task(self.__run_reader_loop())

    # --------------------------------------------------------------------------------
    # Fails every outstanding demux entry at once (a dead connection takes out
    # everything in flight on it, not just whichever caller happened to notice
    # first) and clears the map.
    def __fail_all_outstanding(self, exc: Exception):
        for entry in self.__demux_map.values():
            if not entry.future.done():
                entry.future.set_exception(exc)
        self.__demux_map.clear()

    # --------------------------------------------------------------------------------
    # Mirrors PersistentStreamClientBase's do_heartbeat intent (a bare
    # ping/pong round trip, answered by the server's transport layer alone)
    # but rides the same demux as every other caller -- it cannot perform its
    # own independent read the way the Persisted version does, since the
    # reader loop is now the socket's sole reader.
    async def __do_heartbeat(self):
        try:
            await self.__ensure_connected()
        except (ConnectionRefusedError, OSError):
            return # connection refused

        ping_key                     = SpanKey.generate()
        future                       = asyncio.get_event_loop().create_future()
        self.__demux_map[ping_key]  = _DemuxEntry(future)

        try:
            async with self.__write_lock:
                self.__writer.write(pack_ping_frame(ping_key))
                await self.__writer.drain()

            pong_frame = await asyncio.wait_for(future, self.__timeout)

            _, _, _, flags = parse_header(pong_frame[:HEADER_LENGTH])
            if not (flags & PING_FLAG):
                self.__connected = False
        except (
            ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
            asyncio.IncompleteReadError, OSError, asyncio.TimeoutError,
        ):
            self.__connected = False
        finally:
            self.__demux_map.pop(ping_key, None)

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: bytes) -> bytes:
        span_key    = parse_header(request[:HEADER_LENGTH])[0]
        retry_count = 0

        while retry_count < self.max_retries:
            future                      = asyncio.get_event_loop().create_future()
            try:
                await self.__ensure_connected()
                self.__demux_map[span_key] = _DemuxEntry(future)

                async with self.__write_lock:
                    self.__writer.write(request)
                    await self.__writer.drain()

                # Deliberately NOT raced against a timeout -- an ordinary send
                # has no per-request timeout. See multiplexed_stream_client.md's
                # "Per-request timeout" section: multiplexing means a slow
                # response no longer blocks anything else, and connection
                # death is already handled by __fail_all_outstanding above. A
                # permanently-unanswered entry is a staleness-sweep warning,
                # not a retry trigger.
                response_frame = await future
                self.__demux_map.pop(span_key, None)
                return response_frame
            except (
                ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
                asyncio.IncompleteReadError, OSError, ConnectionRefusedError,
            ) as e:
                self.__demux_map.pop(span_key, None)
                self.__connected = False
                retry_count     += 1
                if retry_count >= self.max_retries:
                    raise CommunicationsMaxRetriesReached() from e
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                self.__demux_map.pop(span_key, None)
                raise CommunicationsNonRetryable(f"{type(e)}: {str(e)}")

        raise CommunicationsMaxRetriesReached()

    # --------------------------------------------------------------------------------
    # Sole reader of the socket it's bound to -- spawned fresh by
    # __ensure_connected() each time it reconnects, rather than one long-lived
    # loop surviving reconnects (see multiplexed_stream_client.md's
    # "Reconnection" section for why).
    async def __run_reader_loop(self):
        try:
            while True:
                header                        = await self.__reader.readexactly(HEADER_LENGTH)
                span_key, _, total_len, _     = parse_header(header)
                rest                          = await self.__reader.readexactly(total_len) if total_len else b""
                frame                         = header + rest

                entry = self.__demux_map.pop(span_key, None)
                if entry is not None and not entry.future.done():
                    entry.future.set_result(frame)
                # else: orphan response (already timed out / stale) -- discarded.
        except asyncio.CancelledError:
            return
        except (asyncio.IncompleteReadError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
            self.__fail_all_outstanding(e)
            self.__connected = False

    # --------------------------------------------------------------------------------
    async def __run_heartbeat_loop(self):
        try:
            while True:
                await asyncio.sleep(self.__heartbeat_period)
                if self.__stopping:
                    return
                await self.__do_heartbeat()
        except asyncio.CancelledError:
            return

    # --------------------------------------------------------------------------------
    # Periodic sweep, structurally mirroring the heartbeat loop. Never removes
    # entries, never retries, never touches the connection -- purely
    # operational visibility. See multiplexed_stream_client.md's "Per-request
    # timeout" section: a permanently-unanswered request is a developer-visible
    # warning, not something the client silently heals.
    async def __run_staleness_sweep_loop(self):
        try:
            while True:
                await asyncio.sleep(self.__staleness_sweep_period)
                if self.__stopping:
                    return

                now = time.monotonic()
                for span_key, entry in self.__demux_map.items():
                    if not entry.warned and (now - entry.registered_at) >= self.__staleness_warning_threshold:
                        entry.warned = True
                        log.warning(
                            f"MultiplexedStreamClientBase: request with span_key {span_key} has been "
                            f"unanswered for over {self.__staleness_warning_threshold}s -- connection is "
                            f"healthy, so this is likely a server-side bug that never wrote a response. "
                            f"Not auto-retried; needs manual investigation."
                        )
        except asyncio.CancelledError:
            return
