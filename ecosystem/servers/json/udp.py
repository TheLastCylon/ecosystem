import asyncio

from ..server_base import ServerBase

from ...configuration.config_models import ConfigUDP
from ...exceptions import IncompleteMessageException


# --------------------------------------------------------------------------------
class UDPServer(asyncio.DatagramProtocol, ServerBase):
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
    def connection_made(self, transport):
        self.__transport = transport

    # --------------------------------------------------------------------------------
    async def __process_received_data(self, received_data: str, address):
        response_dict = await self._route_request(received_data)
        response_str  = response_dict.model_dump_json()
        # self._logger.info(f"Send response:\n {response_str}")
        self.__transport.sendto(response_str.encode(), address)

    # --------------------------------------------------------------------------------
    def datagram_received(self, bytes_read, address):
        # TODO: Check client against white-list
        request_data: str = bytes_read.decode()

        if not request_data.endswith('\n'): # TODO: This makes sense here, but shouldn't the exception be related to Status.PROTOCOL_PARSING_ERROR?
            raise IncompleteMessageException(request_data)

        # self._logger.info(f"Received {request_data} from {address}")
        self.__loop.create_task(self.__process_received_data(request_data, address))

    # --------------------------------------------------------------------------------
    async def __create_datagram_listener(self):
        self._logger.info(f"Serving UDP on [{self.host}:{self.port}]")
        self.__loop = asyncio.get_running_loop()
        self.__transport, protocol = await self.__loop.create_datagram_endpoint(
            lambda: self,
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
