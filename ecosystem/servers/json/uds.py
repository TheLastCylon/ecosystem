import logging
import asyncio
import socket

from ..stream_server_base import StreamServerBase

from ...configuration import ConfigUDS
from ...requests import RequestRouter


# --------------------------------------------------------------------------------
class UDSServer(StreamServerBase):
    def __init__(
        self,
        configuration : ConfigUDS,
        logger        : logging.Logger,
        request_router: RequestRouter,
    ):
        super(UDSServer, self).__init__(logger, request_router)
        self.__server_path  : str  = f"{configuration.directory}/{configuration.socket_file_name}"
        self.__uds_supported: bool = hasattr(socket, "AF_UNIX")

    # --------------------------------------------------------------------------------
    async def __aenter__(self):
        if self.__uds_supported:
            try:
                self._running    = True
                self._logger.info(f"Setting up UDS server.")
                await self.__setup_server()
            except Exception as e:
                self._running = False
                self._server.close()
                raise e
        else:
            self._logger.info(f"UDS not supported on this platform, will not start server.")

    # --------------------------------------------------------------------------------
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.__uds_supported:
            self._running = False
            self._logger.info(f"Stopping UDS server for {self.__server_path}.")
            self._server.close()

    # --------------------------------------------------------------------------------
    async def __setup_server(self):
        self._server   = await asyncio.start_unix_server(self._handle_request, self.__server_path)
        serving_address = self._server.sockets[0].getsockname()
        self._logger.info(f'Serving UDS on {serving_address}')

    # --------------------------------------------------------------------------------
    async def serve(self):
        if self._running:
            async with self._server:
                try:
                    await self._server.serve_forever(),
                except asyncio.exceptions.CancelledError:
                    self._logger.info("UDS Server cancelled.")


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
