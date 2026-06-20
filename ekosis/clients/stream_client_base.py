import logging
import asyncio

from abc import ABC, abstractmethod
from typing import Tuple

from .client_base import ClientBase

from ..data_transfer_objects import HEADER_LENGTH, parse_header

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
    CommunicationsEmptyResponse,
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
class StreamClientBase(ClientBase, ABC):
    def __init__(
        self,
        timeout    : float = 5,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.__timeout = timeout

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        pass

    # --------------------------------------------------------------------------------
    async def _send_message(self, request: bytes) -> bytes:
        reader, writer = await self.open_connection()
        writer.write(request)

        try:
            header = await asyncio.wait_for(reader.readexactly(HEADER_LENGTH), self.__timeout)
        except asyncio.IncompleteReadError:
            raise CommunicationsEmptyResponse()

        _, _, total_len, _ = parse_header(header)
        rest            = await asyncio.wait_for(reader.readexactly(total_len), self.__timeout)

        writer.close()
        await writer.wait_closed()
        return header + rest

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: bytes) -> bytes:
        retry_count = 0
        while retry_count < self.max_retries and not self.success:
            try:
                response = await self._send_message(request)
                self.success = True
                return response
            except (
                TimeoutError,           # Timeouts mean the connection is fine
                asyncio.TimeoutError,   # it's just taking too long. i.e. Retryable.
                ConnectionResetError,   # Reset, abort and broken-pipe are
                ConnectionAbortedError, # retryable forms of ConnectionError
                BrokenPipeError         # ConnectionRefusedError is NOT retryable.
            ):
                retry_count += 1
                if retry_count >= self.max_retries:
                    raise CommunicationsMaxRetriesReached()
                else:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                raise CommunicationsNonRetryable(f"{type(e)}: {str(e)}")
