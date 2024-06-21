import asyncio

from .server_base import ServerBase

from ..exceptions import IncompleteMessageException
from ..exceptions import ClientDisconnectedException


# --------------------------------------------------------------------------------
class StreamServerBase(ServerBase):
    _server: asyncio.Server = None

    def __init__(self):
        super().__init__()

    # --------------------------------------------------------------------------------
    @staticmethod
    async def _read_incoming_request(reader: asyncio.StreamReader) -> str:
        bytes_read = await reader.readline()
        if not bytes_read:
            raise ClientDisconnectedException()

        request_data: str = bytes_read.decode()

        if not request_data.endswith('\n'):
            raise IncompleteMessageException(request_data)

        return request_data

    # --------------------------------------------------------------------------------
    async def _handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            if not self._running:
                return

            requestor_address = writer.get_extra_info('peername')
            request_data      = await self._read_incoming_request(reader) # ClientDisconnectedException, IncompleteMessageException
            self._logger.info(f"_handle_request: Received from {requestor_address}:\n{request_data}")

            response_dict     = await self._route_request(request_data)
            self._logger.info(f"_handle_request: response_dict:\n {response_dict}")
            response_str      = response_dict.json()
            self._logger.info(f"_handle_request: response_str:\n {response_str}")
            writer.write(response_str.encode())
            self._logger.info(f"_handle_request: write done")
            await writer.drain()
            self._logger.info("_handle_request: Closing the connection")
            writer.close()
        except (ClientDisconnectedException, IncompleteMessageException) as e:
            self._logger.info(e.message)
            return
