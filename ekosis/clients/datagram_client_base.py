import asyncio
import logging

from .client_base import ClientBase

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
    CommunicationsEmptyResponse,
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
class DatagramProtocolClient(asyncio.DatagramProtocol):
    def __init__(self, message: str, on_done: asyncio.Future):
        self.message  : str                       = message
        self.on_done  : asyncio.Future            = on_done
        self.transport: asyncio.DatagramTransport = None

    # --------------------------------------------------------------------------------
    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message.encode())

    # --------------------------------------------------------------------------------
    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        if not data:
            self.on_done.set_exception(CommunicationsEmptyResponse())
        else:
            response = data.decode()
            self.on_done.set_result(response)
        self.transport.close()

    # --------------------------------------------------------------------------------
    def error_received(self, exc):
        log.error(f'error_received: Exception: {str(exc)}')
        self.on_done.set_exception(exc)
        self.transport.close()

    # --------------------------------------------------------------------------------
    def connection_lost(self, exc):
        if exc is not None and not self.on_done.done():
            log.error(f'connection_lost: Exception: {str(exc)}')
            self.on_done.set_exception(exc)

# --------------------------------------------------------------------------------
class DatagramClientBase(ClientBase, asyncio.DatagramProtocol):
    def __init__(
        self,
        server_host: str,
        server_port: int,
        timeout    : float = 5,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.server_host: str                       = server_host
        self.server_port: int                       = server_port
        self.timeout    : float                     = timeout
        self.loop       : asyncio.AbstractEventLoop = None
        self.transport  : asyncio.DatagramTransport = None
        self.on_done    : asyncio.Future            = None

    # --------------------------------------------------------------------------------
    async def _send_message(self, message: str) -> str:
        self.loop      = asyncio.get_running_loop()
        self.on_done   = self.loop.create_future()

        self.transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: DatagramProtocolClient(message, self.on_done),
            remote_addr=(self.server_host, self.server_port)
        )

        try:
            response = await asyncio.wait_for(self.on_done, self.timeout)
            return response
        finally:
            if not self.transport.is_closing():
                self.transport.close()

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: str) -> str:
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = await self._send_message(request)
                return response
            except (TimeoutError, asyncio.TimeoutError) as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    raise CommunicationsMaxRetriesReached()
                else:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                raise CommunicationsNonRetryable(str(e))
