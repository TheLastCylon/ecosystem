import asyncio
import logging

from ..server_base import ServerBase

from ...configuration.config_models import ConfigUDP

log = logging.getLogger()

# --------------------------------------------------------------------------------
class DatagramProtocolServer(asyncio.DatagramProtocol):
    __ENQ_byte    : int   =  5 # Decimal  5 = Ascii ENQ (enquiry) character
    __ACK_byte    : int   =  6 # Decimal  6 = Ascii ACK (acknowledge) character
    __LF_byte     : int   = 10 # Decimal 10 = Ascii LF (line feed) character = '\n'
    __ACK_response: bytes = bytes([__ACK_byte, __LF_byte])

    def __init__(self, build_response_function):
        self.build_response_function = build_response_function

        self.transport     : asyncio.DatagramTransport = None
        self.loop          : asyncio.AbstractEventLoop = None
        self.__write_lock  : asyncio.Lock              = asyncio.Lock()

    def connection_made(self, transport):
        self.transport = transport
        self.loop      = asyncio.get_running_loop()

    async def do_response(self, message, addr):
        async with self.__write_lock:
            response = await self.build_response_function(message)
            self.transport.sendto(response.encode(), addr)

    # TODO: find a way to deal with partial bytes read
    def datagram_received(self, bytes_read, addr):
        if bytes_read and bytes_read[-1] == self.__LF_byte:
            if bytes_read[0] == self.__ACK_byte: # The client wants to know we are here.
                self.transport.sendto(self.__ACK_response, addr)
            else:
                request_data: str = bytes_read.decode()
                self.loop.create_task(self.do_response(request_data, addr))

# --------------------------------------------------------------------------------
class UDPServer(ServerBase):
    def __init__(self, configuration : ConfigUDP):
        ServerBase.__init__(self)
        self.host       : str                       = configuration.host
        self.port       : int                       = configuration.port
        self.__transport: asyncio.DatagramTransport = None
        self.__loop     : asyncio.AbstractEventLoop = None

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
    async def __process_received_data(self, received_data: str):
        response_dict = await self._route_request(received_data)
        return response_dict.model_dump_json()

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
