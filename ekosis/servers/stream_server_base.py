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

        if not request_data.endswith('\n'): # TODO: Does this even make sense. We did a readline didn't we?
            raise IncompleteMessageException(request_data)

        return request_data

    # --------------------------------------------------------------------------------
    async def _handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            if not self._running:
                return

            # requestor_address = writer.get_extra_info('peername')
            # TODO: Check client against white-list!
            request_data      = await self._read_incoming_request(reader) # ClientDisconnectedException, IncompleteMessageException
            # self._logger.info(f"_handle_request: Received from {requestor_address}:\n{request_data}")

            response_dict     = await self._route_request(request_data)
            response_str      = response_dict.json()
            writer.write(response_str.encode())
            await writer.drain()
            writer.close()
        except (ClientDisconnectedException, IncompleteMessageException) as e:
            self._logger.info(e.message)
            return
