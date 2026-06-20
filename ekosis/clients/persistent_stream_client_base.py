import time
import asyncio
import logging

from abc import ABC, abstractmethod
from typing import Tuple

from .client_base import ClientBase

from ..data_transfer_objects import HEADER_LENGTH, PING_FLAG, SpanKey, parse_header, pack_ping_frame

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
    CommunicationsEmptyResponse,
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
class PersistentStreamClientBase(ClientBase, ABC):
    def __init__(
        self,
        timeout         : float = 5,
        heartbeat_period: float = 60,
        max_retries     : int   = 3,
        retry_delay     : float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.__timeout       : float                = timeout
        self.__heartbeat_time: float                = heartbeat_period
        self.__connected     : bool                 = False
        self.__last_send     : float                = 0
        self.__read_lock     : asyncio.Lock         = asyncio.Lock()
        self.__write_lock    : asyncio.Lock         = asyncio.Lock()
        self.__reader        : asyncio.StreamReader = None
        self.__writer        : asyncio.StreamWriter = None
        self.__heartbeat_task: asyncio.Task         = None

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
    async def __do_read(self, length: int) -> bytes:
        async with self.__read_lock:
            return await asyncio.wait_for(self.__reader.readexactly(length), self.__timeout)

    # --------------------------------------------------------------------------------
    # A ping is a bare 32-byte frame (no route_key, no body, PING_FLAG set), answered
    # by the transport layer alone on the server side -- never reaching RequestRouter
    # or StatisticsKeeper. Cheap by construction: no msgpack, no routing, just a
    # header round trip. This is the stale-connection detector this class used to do
    # with raw ENQ/ACK bytes, rebuilt on the binary protocol instead.
    async def __do_heartbeat(self):
        try:
            await self.__check_connected() # check if we did connect in the past
        except ConnectionRefusedError:
            return

        try:
            await self.__do_write(pack_ping_frame(SpanKey.generate()))
            pong_header = await self.__do_read(HEADER_LENGTH)
        except (
            asyncio.IncompleteReadError,
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionResetError,
            ConnectionAbortedError,
            BrokenPipeError,
        ):
            self.__connected = False
            return

        _, _, _, flags = parse_header(pong_header)
        if flags & PING_FLAG:
            self.__last_send = time.time()
        else:
            self.__connected = False

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
    async def _send_message(self, request: bytes) -> bytes:
        try:
            await self.__check_connected()
        except ConnectionRefusedError as e:
            raise e

        await self.__do_write(request)

        try:
            header = await self.__do_read(HEADER_LENGTH)
        except asyncio.IncompleteReadError:
            self.__connected = False
            raise CommunicationsEmptyResponse()

        _, _, total_len, _ = parse_header(header)
        rest                = await self.__do_read(total_len)

        self.__last_send = time.time()
        return header + rest

    # --------------------------------------------------------------------------------
    async def __do_retry_logic(self, retry_count: int):
        retry_count += 1
        if retry_count >= self.max_retries:
            raise CommunicationsMaxRetriesReached()
        else:
            await asyncio.sleep(self.retry_delay)
        return retry_count

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: bytes) -> bytes:
        await self.__check_heartbeat_task()

        retry_count = 0
        while retry_count < self.max_retries and not self.success:
            try:
                response = await self._send_message(request)
                self.success = True
                return response
            except (TimeoutError, asyncio.TimeoutError):
                retry_count = await self.__do_retry_logic(retry_count)
            except (
                ConnectionResetError,   # These are retryable exceptions.
                ConnectionAbortedError, # But they mean the connection is broken.
                BrokenPipeError,        # So we have to re-connect.
                CommunicationsEmptyResponse
            ):
                self.__connected = False
                await self.__check_connected()
                retry_count = await self.__do_retry_logic(retry_count)
            except Exception as e:
                raise CommunicationsNonRetryable(f"{type(e)}: {str(e)}")
