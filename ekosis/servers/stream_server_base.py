import asyncio

from .server_base import ServerBase

# --------------------------------------------------------------------------------
class StreamServerBase(ServerBase):
    def __init__(self):
        super().__init__()
        self._server       : asyncio.Server = None
        self.__ENQ_byte    : int            =  5 # Decimal  5 = Ascii ENQ (enquiry) character
        self.__ACK_byte    : int            =  6 # Decimal  6 = Ascii ACK (acknowledge) character
        self.__LF_byte     : int            = 10 # Decimal 10 = Ascii LF (line feed) character = '\n'
        self.__ACK_response: bytes          = bytes([self.__ACK_byte, self.__LF_byte])
        self.__read_lock   : asyncio.Lock   = asyncio.Lock()
        self.__write_lock  : asyncio.Lock   = asyncio.Lock()

    # --------------------------------------------------------------------------------
    async def __read_data(self, reader: asyncio.StreamReader):
        async with self.__read_lock:
            return await reader.readline()

    # --------------------------------------------------------------------------------
    async def __write_data(self, writer: asyncio.StreamWriter, data: bytes):
        async with self.__write_lock:
            writer.write(data)
            await writer.drain()

    # TODO: Check client against white-list!
    # --------------------------------------------------------------------------------
    async def _handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if not self._running:
            return
        while True: # We keep the connection open.
            try:
                bytes_read = await reader.readline()

                # Check if the client closed the connection.
                # Take note: An incomplete read due to EOF is treated as a client disconnect,
                # So we check if the last byte read is '\n' i.e. Decimal 10/Ascii symbol: LF
                if not bytes_read or bytes_read[-1] != self.__LF_byte:
                    break

                if bytes_read[0] == self.__ENQ_byte: # The client is asking if we are still connected.
                    await self.__write_data(writer, self.__ACK_response)
                else:
                    response_dict = await self._route_request(bytes_read.decode())
                    await self.__write_data(
                        writer,
                        (response_dict.model_dump_json() + '\n').encode()
                    )
            except ConnectionResetError:
                self._logger.info("Connection reset by peer")
                break
        writer.close()
