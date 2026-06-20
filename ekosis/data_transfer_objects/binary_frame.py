import struct
import msgpack

from typing import Tuple

from .json_protocol import SpanKey, ResponseDTO

HEADER_LENGTH: int = 32   # 24B SpanKey + 4B total_len + 1B route_key_len + 1B flags + 2B reserved
PING_FLAG    : int = 0x01 # Liveness probe -- answered by the transport layer alone, never routed.

# --------------------------------------------------------------------------------
def pack_frame(span_key: SpanKey, route_key: str, body: bytes, flags: int = 0) -> bytes:
    route_key_bytes: bytes = route_key.encode()
    route_key_len  : int   = len(route_key_bytes)
    total_len      : int   = route_key_len + len(body)
    header         : bytes = (
        span_key.bytes +
        struct.pack(">IBB2s", total_len, route_key_len, flags, b"\x00\x00")
    )
    return header + route_key_bytes + body

# --------------------------------------------------------------------------------
def parse_header(header: bytes) -> Tuple[SpanKey, int, int, int]:
    span_key                                = SpanKey.from_bytes(header[0:24])
    total_len, route_key_len, flags, _ = struct.unpack(">IBB2s", header[24:32])
    return span_key, route_key_len, total_len, flags

# --------------------------------------------------------------------------------
def split_route_key_and_body(data: bytes, route_key_len: int) -> Tuple[str, bytes]:
    route_key: str   = data[:route_key_len].decode()
    body     : bytes = data[route_key_len:]
    return route_key, body

# --------------------------------------------------------------------------------
# route_key="" marks this as a response frame -- a response is never routed, so an
# empty route_key says everything that needs saying about that.
def pack_response_frame(response: ResponseDTO) -> bytes:
    body: bytes = msgpack.packb(response.model_dump(mode="json", exclude={"span_key"}))
    return pack_frame(response.span_key, "", body)

# --------------------------------------------------------------------------------
# A ping/pong frame: no route_key, no body, PING_FLAG set -- a pure 32-byte liveness
# probe. The same shape is used in both directions; whoever receives a PING_FLAG
# frame echoes one straight back, never touching RequestRouter or msgpack.
def pack_ping_frame(span_key: SpanKey) -> bytes:
    return pack_frame(span_key, "", b"", flags=PING_FLAG)
