import asyncio
import socket
import msgpack
import pytest

from ekosis.data_transfer_objects import SpanKey, HEADER_LENGTH, pack_frame, parse_header, split_route_key_and_body
from ekosis.requests.status import Status

TCP_HOST: str = '127.0.0.1'
TCP_PORT: int = 8888
UDP_HOST: str = '127.0.0.1'
UDP_PORT: int = 8889

# These tests talk the binary frame directly over raw sockets, bypassing the
# ekosis clients entirely -- they exist to exercise the malformed-frame and
# mid-frame-disconnect paths in the server's framing layer, which a well-behaved
# client never triggers.

# --------------------------------------------------------------------------------
async def _send_raw_tcp_frame(frame: bytes) -> bytes:
    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
    writer.write(frame)
    await writer.drain()

    header = await asyncio.wait_for(reader.readexactly(HEADER_LENGTH), 5)
    _, route_key_len, total_len, _ = parse_header(header)
    rest   = await asyncio.wait_for(reader.readexactly(total_len), 5)

    writer.close()
    await writer.wait_closed()
    return header + rest

# --------------------------------------------------------------------------------
def _unpack_response(frame: bytes):
    span_key, route_key_len, total_len, _ = parse_header(frame[:HEADER_LENGTH])
    _, body = split_route_key_and_body(frame[HEADER_LENGTH:HEADER_LENGTH + total_len], route_key_len)
    return span_key, msgpack.unpackb(body, raw=False)

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_malformed_msgpack_body_tcp_returns_parsing_error():
    span_key       = SpanKey.generate()
    frame          = pack_frame(span_key, "app.a.endpoint", bytes([0xc1, 0xc1, 0xc1])) # 0xc1 is reserved/invalid in msgpack.
    response_frame = await _send_raw_tcp_frame(frame)

    response_span_key, response_dict = _unpack_response(response_frame)

    assert response_span_key == span_key
    assert response_dict["status"] == Status.PROTOCOL_PARSING_ERROR.value

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tcp_disconnect_mid_header_does_not_hang_server():
    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
    writer.write(b"\x00" * 10) # Less than HEADER_LENGTH -- never completes a header.
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    # If the partial-header disconnect above left the server hung or broken, this
    # normal request -- on a fresh connection -- would time out or fail.
    span_key          = SpanKey.generate()
    frame             = pack_frame(span_key, "app.a.endpoint", msgpack.packb({"message": "still alive"}))
    response_frame    = await _send_raw_tcp_frame(frame)
    _, response_dict  = _unpack_response(response_frame)
    assert response_dict["status"] == Status.SUCCESS.value

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tcp_disconnect_mid_body_does_not_hang_server():
    span_key = SpanKey.generate()
    header   = pack_frame(span_key, "app.a.endpoint", b"x" * 100)[:HEADER_LENGTH] # Promises >100 body bytes.

    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
    writer.write(header + b"only_ten_b") # Deliver 10 of the promised bytes, then disconnect.
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    frame             = pack_frame(SpanKey.generate(), "app.a.endpoint", msgpack.packb({"message": "still alive"}))
    response_frame    = await _send_raw_tcp_frame(frame)
    _, response_dict  = _unpack_response(response_frame)
    assert response_dict["status"] == Status.SUCCESS.value

# --------------------------------------------------------------------------------
def test_malformed_msgpack_body_udp_returns_parsing_error():
    span_key = SpanKey.generate()
    frame    = pack_frame(span_key, "app.a.endpoint", bytes([0xc1, 0xc1, 0xc1]))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(frame, (UDP_HOST, UDP_PORT))
    response_frame, _ = sock.recvfrom(4096)
    sock.close()

    response_span_key, response_dict = _unpack_response(response_frame)
    assert response_span_key == span_key
    assert response_dict["status"] == Status.PROTOCOL_PARSING_ERROR.value

# --------------------------------------------------------------------------------
def test_udp_packet_shorter_than_header_is_dropped():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(b"\x00" * 10, (UDP_HOST, UDP_PORT)) # Shorter than HEADER_LENGTH -- not a valid frame.

    with pytest.raises(socket.timeout): # No response should ever arrive for this packet.
        sock.recvfrom(4096)
    sock.close()
