import asyncio

from .client_base import ClientBase

from ..exceptions import (
    CommunicationsNonRetryable,
    CommunicationsMaxRetriesReached,
    CommunicationsEmptyResponse,
)


# --------------------------------------------------------------------------------
class DatagramClientBase(ClientBase, asyncio.DatagramProtocol):
    server_host: str                       = None
    server_port: int                       = None
    loop       : asyncio.AbstractEventLoop = None
    transport  : asyncio.DatagramTransport = None
    on_done    : asyncio.Future            = None
    request    : str                       = None

    def __init__(
        self,
        server_host: str,
        server_port: int,
        timeout    : float = 1,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.server_host = server_host
        self.server_port = server_port
        self.timeout     = timeout

    # --------------------------------------------------------------------------------
    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport
        self.transport.sendto(self.request.encode())

    # --------------------------------------------------------------------------------
    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        if not data:
            self.on_done.set_exception(CommunicationsEmptyResponse())
        else:
            response = data.decode()
            self.transport.close()
            self.on_done.set_result(response)

    # --------------------------------------------------------------------------------
    def error_received(self, exc):
        print(f'error_received: Exception: {str(exc)}')
        self.on_done.set_exception(exc)

    # --------------------------------------------------------------------------------
    def connection_lost(self, exc):
        if exc:
            print(f'connection_lost: Exception: {str(exc)}')
            self.on_done.set_exception(exc)
        elif not self.on_done.done():
            print('connection_lost: Exception: Connection lost')
            self.on_done.set_exception(Exception('Connection lost')) # TODO: Improve this exception

    # --------------------------------------------------------------------------------
    async def _send_message(self) -> str:
        self.loop    = asyncio.get_running_loop()
        self.on_done = self.loop.create_future()

        self.transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: self,
            remote_addr=(self.server_host, self.server_port)
        )

        try:
            return await asyncio.wait_for(self.on_done, timeout=self.timeout)
        finally:
            self.transport.close()

    # --------------------------------------------------------------------------------
    async def _send_message_retry_loop(self, request: str) -> str:
        self.request = request
        while self.retry_count < self.max_retries and not self.success:
            try:
                response     = await self._send_message()
                self.success = True
                return response
            except (TimeoutError, asyncio.TimeoutError) as e:
                await asyncio.sleep(self.retry_delay)
                self.retry_count += 1
            except Exception as e:
                raise CommunicationsNonRetryable(str(e))

        if not self.success:
            if self.retry_count >= self.max_retries:
                raise CommunicationsMaxRetriesReached()
