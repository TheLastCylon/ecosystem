import asyncio
import msgpack

from .server_base import ServerBase

from ..data_transfer_objects import (
    HEADER_LENGTH,
    PING_FLAG,
    MAX_FRAME_SIZE,
    parse_header,
    split_route_key_and_body,
    pack_response_frame,
    pack_ping_frame,
)

# --------------------------------------------------------------------------------
class StreamServerBase(ServerBase):
    def __init__(self):
        super().__init__()
        self._server: asyncio.Server = None

    # --------------------------------------------------------------------------------
    async def __write_data(self, writer: asyncio.StreamWriter, data: bytes):
        writer.write(data)
        await writer.drain()

    # --------------------------------------------------------------------------------
    async def _handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if not self._running:
            return
        while True: # We keep the connection open.
            try:
                header = await reader.readexactly(HEADER_LENGTH)
            except (asyncio.IncompleteReadError, ConnectionResetError):
                break

            span_key, route_key_len, total_len, flags = parse_header(header)

            if flags & PING_FLAG: # A liveness probe: answer it directly, never reaching _route_request.
                await self.__write_data(writer, pack_ping_frame(span_key))
                continue

            # total_len is attacker/bug-controlled (4 bytes straight off the wire, max
            # ~4GB) -- reject before allocating rather than let readexactly() itself
            # block trying to fill an oversized buffer.
            if total_len > MAX_FRAME_SIZE:
                response = self._build_parsing_error_response(span_key, ValueError("total_len exceeds MAX_FRAME_SIZE"))
                await self.__write_data(writer, pack_response_frame(response))
                break # Can't trust this stream's framing beyond this point, close it.

            try:
                rest = await reader.readexactly(total_len)
            except (asyncio.IncompleteReadError, ConnectionResetError):
                break

            route_key, body = split_route_key_and_body(rest, route_key_len)

            try:
                data = msgpack.unpackb(body, raw=False)
            except Exception as e:
                response = self._build_parsing_error_response(span_key, e)
            else:
                response = await self._route_request(span_key, route_key, data)

            await self.__write_data(writer, pack_response_frame(response))
        writer.close()
