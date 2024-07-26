import asyncio

from typing import Tuple
from ..persistent_stream_client_base import PersistentStreamClientBase

# --------------------------------------------------------------------------------
class PersistedTCPClient(PersistentStreamClientBase):
    def __init__(
        self,
        server_host: str,
        server_port: int,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        self.server_host: str   = server_host
        self.server_port: int   = server_port
        super().__init__(max_retries, retry_delay)

    # --------------------------------------------------------------------------------
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_connection(self.server_host, self.server_port)
