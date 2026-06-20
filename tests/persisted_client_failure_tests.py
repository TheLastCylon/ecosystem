import time
import asyncio
import socket
import struct
import msgpack
import pytest

from ekosis.clients import PersistedTCPClient
from ekosis.data_transfer_objects import HEADER_LENGTH, SpanKey, EmptyDto, parse_header, pack_frame
from ekosis.requests.status import Status

# These tests exercise PersistentStreamClientBase's own failure-handling branches --
# refused connections, silent/malformed pongs, and mid-response resets -- none of
# which a well-behaved ekosis server ever triggers. A small "broken on purpose" TCP
# server stands in for one. Heartbeat internals are reached via their mangled names
# directly rather than waited-for on a timer -- the alternative (tiny heartbeat_period
# + sleep-and-hope) is timing-dependent and flaky; this is deterministic.

# --------------------------------------------------------------------------------
class _FlakyServer:
    def __init__(self, handler):
        self._handler        = handler
        self._server         : asyncio.AbstractServer = None
        self.host            : str = '127.0.0.1'
        self.port            : int = 0
        self.connection_count: int = 0

    async def __aenter__(self):
        async def _on_connect(reader, writer):
            self.connection_count += 1
            await self._handler(reader, writer)

        self._server = await asyncio.start_server(_on_connect, self.host, 0)
        self.port    = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._server.close()
        await self._server.wait_closed()

# --------------------------------------------------------------------------------
async def _accept_and_close_silently(reader, writer):
    await reader.read(HEADER_LENGTH) # Read the ping, then go silent -- no pong at all.
    writer.close()

# --------------------------------------------------------------------------------
async def _accept_and_pong_without_flag(reader, writer):
    header           = await reader.readexactly(HEADER_LENGTH)
    span_key, _, _, _ = parse_header(header)
    bad_pong         = pack_frame(span_key, "", b"") # Same shape as a ping, but PING_FLAG NOT set.
    writer.write(bad_pong)
    await writer.drain()
    writer.close()

# --------------------------------------------------------------------------------
async def _accept_then_reset(reader, writer):
    await reader.read(HEADER_LENGTH)
    sock = writer.get_extra_info('socket')
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0)) # Force RST, not FIN.
    writer.close()

# --------------------------------------------------------------------------------
async def _accept_and_respond_success(reader, writer):
    header                             = await reader.readexactly(HEADER_LENGTH)
    span_key, route_key_len, total_len, _ = parse_header(header)
    await reader.readexactly(total_len) # Drain the request -- content doesn't matter here.
    body = msgpack.packb({"status": Status.SUCCESS.value, "data": {}})
    writer.write(pack_frame(span_key, "", body))
    await writer.drain()
    writer.close()

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_connection_refused():
    # Nothing is listening on this port -- open_connection() raises ConnectionRefusedError.
    client = PersistedTCPClient(server_host='127.0.0.1', server_port=1, heartbeat_period=60)
    await client._PersistentStreamClientBase__do_heartbeat() # Must swallow the refusal, not raise.

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_silent_server():
    async with _FlakyServer(_accept_and_close_silently) as server:
        client = PersistedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=60)
        await client._PersistentStreamClientBase__do_heartbeat()
        assert client._PersistentStreamClientBase__connected is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_pong_without_ping_flag():
    async with _FlakyServer(_accept_and_pong_without_flag) as server:
        client = PersistedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=60)
        await client._PersistentStreamClientBase__do_heartbeat()
        assert client._PersistentStreamClientBase__connected is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_persisted_client_reconnects_after_reset():
    call_count = {"count": 0}

    async def _handler(reader, writer):
        call_count["count"] += 1
        if call_count["count"] == 1:
            await _accept_then_reset(reader, writer)
        else:
            await _accept_and_respond_success(reader, writer)

    async with _FlakyServer(_handler) as server:
        client = PersistedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=9999)
        # __last_send defaults to 0, so the background heartbeat's very first check
        # always fires immediately regardless of heartbeat_period -- seed it so the
        # heartbeat doesn't race the request below and add a spurious connection.
        client._PersistentStreamClientBase__last_send = time.time()

        response = await client.send_message("does.not.matter", EmptyDto(), EmptyDto, SpanKey.generate())

        assert isinstance(response, EmptyDto)
        assert server.connection_count == 2 # First connection reset, second succeeded.
