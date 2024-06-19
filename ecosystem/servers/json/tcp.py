import logging
import asyncio

from ..stream_server_base import StreamServerBase
from ...requests import RequestRouter


# --------------------------------------------------------------------------------
class TCPServer(StreamServerBase):
    def __init__(
        self,
        host          : str,
        port          : int,
        logger        : logging.Logger,
        request_router: RequestRouter,
    ):
        super().__init__(logger, request_router)
        self.host             : str                         = host
        self.port             : int                         = port

    # --------------------------------------------------------------------------------
    async def __aenter__(self):
        try:
            self._running    = True
            self._logger.info(f"Setting up TCP server.")
            await self.__setup_server()
        except Exception as e:
            self._running = False
            self._server.close()
            raise e

    # --------------------------------------------------------------------------------
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._running = False
        self._logger.info(f"Stopping TCP server for {self.host}:{self.port}.")
        self._server.close()

    # --------------------------------------------------------------------------------
    async def __setup_server(self):
        self._server   = await asyncio.start_server(self._handle_request, self.host, self.port)
        serving_address = self._server.sockets[0].getsockname()
        self._logger.info(f'Serving on {serving_address}')

    # --------------------------------------------------------------------------------
    async def serve(self):
        if self._running:
            async with self._server:
                try:
                    await self._server.serve_forever(),
                except asyncio.exceptions.CancelledError:
                    self._logger.info("TCP server cancelled.")


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
