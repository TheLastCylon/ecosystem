import time
import asyncio
import socket
import struct
import msgpack
import pytest

from pydantic import BaseModel as PydanticBaseModel

from ekosis.clients import MultiplexedTCPClient
from ekosis.data_transfer_objects import HEADER_LENGTH, SpanKey, EmptyDto, parse_header, pack_frame, split_route_key_and_body
from ekosis.requests.status import Status

# These tests exercise MultiplexedStreamClientBase's own machinery -- refused
# connections, silent/malformed pongs, mid-response resets, and (the coverage
# ekocpp's own smoke test is still missing, per its "still needs deciding"
# notes) genuine concurrent demux under load. A small "broken on purpose" TCP
# server stands in for a real one, same pattern as persisted_client_failure_tests.py.
# Heartbeat internals are reached via their mangled names directly, deterministic
# rather than timing-dependent.

# --------------------------------------------------------------------------------
class _ValueRequestDto(PydanticBaseModel):
    value: int

# --------------------------------------------------------------------------------
class _ValueResponseDto(PydanticBaseModel):
    value: int

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
# Reads requests back-to-back without waiting for each reply -- genuine
# pipelining on the server side, mirroring what the client is doing. Replies
# are scheduled in REVERSE order of arrival (the request carrying the smallest
# value waits longest), so a client that demuxes correctly gets back exactly
# its own value regardless of reply order; a client that doesn't (e.g. a
# single shared response slot) would see values scrambled or duplicated.
async def _multiplexing_echo_server(reader, writer):
    async def _delayed_reply(span_key, value, delay):
        await asyncio.sleep(delay)
        body = msgpack.packb({"status": Status.SUCCESS.value, "data": {"value": value}})
        writer.write(pack_frame(span_key, "", body))
        await writer.drain()

    while True:
        try:
            # A quiet-period timeout, not a per-request one -- once no new
            # request has arrived for a bit, assume the client is done and
            # return, closing this connection. Without this the handler loops
            # forever waiting for a request that never comes, and Python 3.12+'s
            # Server.wait_closed() waits for every accepted connection's handler
            # to actually finish (not just the listening socket) -- so
            # _FlakyServer.__aexit__ would hang forever on this one connection.
            header = await asyncio.wait_for(reader.readexactly(HEADER_LENGTH), timeout=1.0)
        except asyncio.IncompleteReadError:
            return # peer already closed its side
        except asyncio.TimeoutError:
            writer.close() # we're choosing to stop -- the transport is still open, so close it ourselves
            return
        span_key, route_key_len, total_len, _ = parse_header(header)
        rest                                  = await reader.readexactly(total_len)
        _, body                               = split_route_key_and_body(rest, route_key_len)
        value                                 = msgpack.unpackb(body, raw=False)["value"]
        asyncio.create_task(_delayed_reply(span_key, value, (9 - value) * 0.02))

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_connection_refused():
    # Nothing is listening on this port -- open_connection() raises ConnectionRefusedError.
    client = MultiplexedTCPClient(server_host='127.0.0.1', server_port=1, heartbeat_period=60)
    await client._MultiplexedStreamClientBase__do_heartbeat() # Must swallow the refusal, not raise.

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_silent_server():
    async with _FlakyServer(_accept_and_close_silently) as server:
        client = MultiplexedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=60, timeout=1)
        await client._MultiplexedStreamClientBase__do_heartbeat()
        assert client._MultiplexedStreamClientBase__connected is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_heartbeat_handles_pong_without_ping_flag():
    async with _FlakyServer(_accept_and_pong_without_flag) as server:
        client = MultiplexedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=60)
        await client._MultiplexedStreamClientBase__do_heartbeat()
        assert client._MultiplexedStreamClientBase__connected is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multiplexed_client_reconnects_after_reset():
    call_count = {"count": 0}

    async def _handler(reader, writer):
        call_count["count"] += 1
        if call_count["count"] == 1:
            await _accept_then_reset(reader, writer)
        else:
            await _accept_and_respond_success(reader, writer)

    async with _FlakyServer(_handler) as server:
        client = MultiplexedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=9999)

        response = await client.send_message("does.not.matter", EmptyDto(), EmptyDto, SpanKey.generate())

        assert isinstance(response, EmptyDto)
        assert server.connection_count == 2 # First connection reset, second succeeded.

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_requests_demux_correctly_even_out_of_order():
    async with _FlakyServer(_multiplexing_echo_server) as server:
        client = MultiplexedTCPClient(server_host=server.host, server_port=server.port, heartbeat_period=9999)

        async def _send(value: int) -> int:
            response = await client.send_message(
                "does.not.matter", _ValueRequestDto(value=value), _ValueResponseDto, SpanKey.generate()
            )
            return response.value

        results = await asyncio.gather(*(_send(value) for value in range(10)))

        assert results == list(range(10)) # Each caller got back exactly its own value.
        assert server.connection_count == 1 # All 10 requests genuinely shared one connection.

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_connection_death_fails_all_outstanding_requests():
    # Accepts, reads nothing further, then closes -- every in-flight request on
    # this connection should fail together, not just whichever one the reader
    # loop happened to notice first.
    async def _accept_then_go_silent_forever(reader, writer):
        await asyncio.sleep(0.1) # Let all sends land before the connection dies.
        writer.close()

    async with _FlakyServer(_accept_then_go_silent_forever) as server:
        client = MultiplexedTCPClient(
            server_host=server.host, server_port=server.port, heartbeat_period=9999, max_retries=1, retry_delay=0
        )

        async def _send(value: int):
            try:
                await client.send_message(
                    "does.not.matter", _ValueRequestDto(value=value), _ValueResponseDto, SpanKey.generate()
                )
                return "unexpected_success"
            except Exception:
                return "failed"

        results = await asyncio.gather(*(_send(value) for value in range(5)))

        assert results == ["failed"] * 5 # All 5 outstanding requests failed together.
