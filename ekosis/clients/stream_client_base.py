import logging
import asyncio

from abc import ABC, abstractmethod
from typing import Tuple

from .client_base import ClientBase

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
    async def _send_message(self, request: str) -> str:
        reader, writer = await self.open_connection()
        writer.write(request.encode())

        data = await asyncio.wait_for(reader.readline(), self.__timeout)
        if not data:
            raise CommunicationsEmptyResponse()

        response_str = data.decode()
        writer.close()
        await writer.wait_closed()
        return response_str

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: str) -> str:
        retry_count = 0
        while retry_count < self.max_retries and not self.success:
            try:
                response_str = await self._send_message(request)
                self.success = True
                return response_str
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
