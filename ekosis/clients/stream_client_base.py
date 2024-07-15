import asyncio

from abc import ABC, abstractmethod
from typing import Tuple

from .client_base import ClientBase

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
    CommunicationsEmptyResponse,
)


# --------------------------------------------------------------------------------
class StreamClientBase(ClientBase, ABC):
    def __init__(
        self,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        pass

    # --------------------------------------------------------------------------------
    async def _send_message(self, request: str) -> str:
        reader, writer = await self.open_connection()
        writer.write(request.encode())

        data = await reader.readline()
        if not data:
            raise CommunicationsEmptyResponse()

        response_str = data.decode()
        writer.close()
        await writer.wait_closed()
        return response_str

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: str) -> str:
        while self.retry_count < self.max_retries and not self.success:
            try:
                response_str = await self._send_message(request)
                self.success = True
                return response_str
            except (TimeoutError, ConnectionResetError, BrokenPipeError, asyncio.TimeoutError) as e:
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    raise CommunicationsMaxRetriesReached()
                else:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                raise CommunicationsNonRetryable(str(e))
