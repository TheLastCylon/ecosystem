import asyncio
import logging

from .client_base import ClientBase

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
class DatagramProtocolClient(asyncio.DatagramProtocol):
    def __init__(self):
        self.response : asyncio.Future            = None
        self.transport: asyncio.DatagramTransport = None

    # --------------------------------------------------------------------------------
    def connection_made(self, transport):
        self.transport = transport

    # --------------------------------------------------------------------------------
    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        if self.response:
            self.response.set_result(data.decode())
            self.response = None

    # --------------------------------------------------------------------------------
    def send_message(self, message: str):
        if self.transport is not None:
            self.response = asyncio.Future()
            self.transport.sendto(message.encode())
            return self.response
        else:
            return None

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
        self.initialised: bool                      = False
        self.loop       : asyncio.AbstractEventLoop = None
        self.transport  : asyncio.DatagramTransport = None
        self.protocol   : DatagramProtocolClient    = None
        self.send_lock  : asyncio.Lock              = asyncio.Lock()

    # --------------------------------------------------------------------------------
    async def _send_message(self, message: str) -> str:
        if not self.initialised:
            self.loop            = asyncio.get_running_loop()
            self.transport, self.protocol = await self.loop.create_datagram_endpoint(
                lambda: DatagramProtocolClient(),
                remote_addr=(self.server_host, self.server_port)
            )
            self.initialised = True

        async with self.send_lock:
            return await self.protocol.send_message(message)

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
