import asyncio
import msgpack

from .server_base import ServerBase

from ..data_transfer_objects import (
    HEADER_LENGTH, PING_FLAG, parse_header, split_route_key_and_body, pack_response_frame, pack_ping_frame,
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

    # TODO: Check client against white-list!
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

            if flags & PING_FLAG: # A liveness probe -- answer it directly, never reaching _route_request.
                await self.__write_data(writer, pack_ping_frame(span_key))
                continue

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
