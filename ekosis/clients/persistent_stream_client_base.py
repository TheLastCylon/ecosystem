import time
import asyncio
import logging

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
class PersistentStreamClientBase(ClientBase, ABC):
    __ENQ_byte   : int   =  5 # Decimal  5 = Ascii ENQ (enquiry) character
    __ACK_byte   : int   =  6 # Decimal  6 = Ascii ACK (acknowledge) character
    __LF_byte    : int   = 10 # Decimal 10 = Ascii LF (line feed) character = '\n'
    __ENQ_request: bytes = bytes([__ENQ_byte, __LF_byte])

    def __init__(
        self,
        timeout         : float = 5,
        heartbeat_period: float = 60,
        max_retries     : int   = 3,
        retry_delay     : float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.__timeout          : float                = timeout
        self.__heartbeat_time   : float                = heartbeat_period
        self.__connected        : bool                 = False
        self.__last_send        : float                = 0
        self.__read_lock        : asyncio.Lock         = asyncio.Lock()
        self.__write_lock       : asyncio.Lock         = asyncio.Lock()
        self.__reader           : asyncio.StreamReader = None
        self.__writer           : asyncio.StreamWriter = None
        self.__heartbeat_task   : asyncio.Task         = None

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]: # pragma: no cover
        pass

    # --------------------------------------------------------------------------------
    async def close_connection(self):
        self.__writer.close()
        await self.__writer.wait_closed()

    # --------------------------------------------------------------------------------
    async def __check_connected(self):
        if not self.__connected:
            self.__reader, self.__writer = await self.open_connection()
            self.__connected = True

    # --------------------------------------------------------------------------------
    async def __do_write(self, data: bytes):
        async with self.__write_lock:
            self.__writer.write(data)

    # --------------------------------------------------------------------------------
    async def __do_read(self) -> bytes:
        async with self.__read_lock:
            return await asyncio.wait_for(self.__reader.readline(), self.__timeout) # There needs to be a timeout here.

    # --------------------------------------------------------------------------------
    async def __do_heartbeat(self):
        try:
            await self.__check_connected() # check if we did connect in the past
        except ConnectionRefusedError as e:
            return

        await self.__do_write(self.__ENQ_request)

        data = await self.__do_read()

        if (
            not data or
            data[-1] != self.__LF_byte or
            data[0]  != self.__ACK_byte
        ):
            self.__connected = False
        else:
            self.__last_send = time.time()

    # --------------------------------------------------------------------------------
    async def __heartbeat_check(self):
        while True:
            last_acceptable_send_time = time.time() - self.__heartbeat_time
            if self.__last_send < last_acceptable_send_time:
                await self.__do_heartbeat()
            await asyncio.sleep(self.__heartbeat_time)

    # --------------------------------------------------------------------------------
    async def __check_heartbeat_task(self):
        if self.__heartbeat_task is None or self.__heartbeat_task.done():
            loop = asyncio.get_event_loop()
            self.__heartbeat_task = loop.create_task(self.__heartbeat_check())

    # --------------------------------------------------------------------------------
    async def _send_message(self, request: str) -> str:
        try:
            await self.__check_connected()
        except ConnectionRefusedError as e:
            raise e

        await self.__do_write(request.encode())

        data = await self.__do_read()
        if not data or data[-1] != self.__LF_byte:
            self.__connected = False
            raise CommunicationsEmptyResponse()

        self.__last_send = time.time()
        response_str = data.decode()
        return response_str

    # --------------------------------------------------------------------------------
    async def __do_retry_logic(self, retry_count: int):
        retry_count += 1
        if retry_count >= self.max_retries:
            raise CommunicationsMaxRetriesReached()
        else:
            await asyncio.sleep(self.retry_delay)
        return retry_count

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: str) -> str:
        await self.__check_heartbeat_task()

        retry_count = 0
        while retry_count < self.max_retries and not self.success:
            try:
                response_str = await self._send_message(request)
                self.success = True
                return response_str
            except (TimeoutError, asyncio.TimeoutError):
                retry_count = self.__do_retry_logic(retry_count)
            except (
                ConnectionResetError,   # These are retryable exceptions.
                ConnectionAbortedError, # But they mean the connection is broken.
                BrokenPipeError,        # So we have to re-connect.
                CommunicationsEmptyResponse
            ):
                self.__connected = False
                await self.__check_connected()
                retry_count = self.__do_retry_logic(retry_count)
            except Exception as e:
                raise CommunicationsNonRetryable(f"{type(e)}: {str(e)}")
