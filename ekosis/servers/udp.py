import asyncio
import logging
import msgpack

from .server_base import ServerBase

from ..configuration.config_models import ConfigUDP
from ..data_transfer_objects import (
    SpanKey, HEADER_LENGTH, PING_FLAG, parse_header, split_route_key_and_body,
    pack_response_frame, pack_ping_frame,
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
class DatagramProtocolServer(asyncio.DatagramProtocol):
    def __init__(self, build_response_function):
        self.build_response_function = build_response_function

        self.transport     : asyncio.DatagramTransport = None
        self.loop          : asyncio.AbstractEventLoop = None
        self.__write_lock  : asyncio.Lock              = asyncio.Lock()

    def connection_made(self, transport):
        self.transport = transport
        self.loop      = asyncio.get_running_loop()

    async def do_response(self, span_key: SpanKey, route_key: str, body: bytes, addr):
        async with self.__write_lock:
            response = await self.build_response_function(span_key, route_key, body)
            self.transport.sendto(response, addr)

    # A UDP packet is already datagram-bounded, so the whole frame is in memory up
    # front -- no incremental reads needed, just slice the fixed header off the front.
    def datagram_received(self, bytes_read, addr):
        if len(bytes_read) < HEADER_LENGTH:
            return # Too short to even hold a header -- not a valid frame, drop it.

        span_key, route_key_len, total_len, flags = parse_header(bytes_read[:HEADER_LENGTH])

        if flags & PING_FLAG: # A liveness probe -- answer it directly, never reaching __process_received_data.
            self.transport.sendto(pack_ping_frame(span_key), addr)
            return

        rest            = bytes_read[HEADER_LENGTH:HEADER_LENGTH + total_len]
        route_key, body = split_route_key_and_body(rest, route_key_len)

        self.loop.create_task(self.do_response(span_key, route_key, body, addr))

# --------------------------------------------------------------------------------
class UDPServer(ServerBase):
    def __init__(self, configuration : ConfigUDP):
        ServerBase.__init__(self)
        self.host       : str                       = configuration.host
        self.port       : int                       = configuration.port
        self.__transport: asyncio.DatagramTransport = None
        self.__loop     : asyncio.AbstractEventLoop = None
        self.set_transport_type("UDP")

    # --------------------------------------------------------------------------------
    async def __aenter__(self):
        self._running = True
        self._logger.info(f"Setting up UDP server.")

    # --------------------------------------------------------------------------------
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    # --------------------------------------------------------------------------------
    def stop(self):
        if self._running:
            self._running = False
            self._logger.info(f"Stopping UDP server for {self.host}:{self.port}.")

    # --------------------------------------------------------------------------------
    async def __process_received_data(self, span_key: SpanKey, route_key: str, body: bytes) -> bytes:
        try:
            data = msgpack.unpackb(body, raw=False)
        except Exception as e:
            response = self._build_parsing_error_response(span_key, e)
        else:
            response = await self._route_request(span_key, route_key, data)
        return pack_response_frame(response)

    # --------------------------------------------------------------------------------
    async def __create_datagram_listener(self):
        self._logger.info(f"Serving UDP on [{self.host}:{self.port}]")
        self.__loop = asyncio.get_running_loop()
        self.__transport, protocol = await self.__loop.create_datagram_endpoint(
            lambda: DatagramProtocolServer(self.__process_received_data),
            local_addr=(self.host, self.port)
        )

        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.exceptions.CancelledError:
            self._logger.info("UDP server cancelled.")
        finally:
            self.__transport.close()

    # --------------------------------------------------------------------------------
    async def serve(self):
        if self._running:
            await self.__create_datagram_listener()
