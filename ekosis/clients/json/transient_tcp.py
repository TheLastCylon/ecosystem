import asyncio

from typing import Tuple
from ..stream_client_base import StreamClientBase

# --------------------------------------------------------------------------------
class TransientTCPClient(StreamClientBase):
    def __init__(
        self,
        server_host: str,
        server_port: int,
        timeout    : float = 5,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(timeout, max_retries, retry_delay)
        self.server_host: str   = server_host
        self.server_port: int   = server_port

    # --------------------------------------------------------------------------------
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_connection(self.server_host, self.server_port)
