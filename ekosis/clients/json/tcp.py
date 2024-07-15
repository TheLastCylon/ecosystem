import asyncio

from typing import Tuple
from ..stream_client_base import StreamClientBase


# --------------------------------------------------------------------------------
class TCPClient(StreamClientBase):
    def __init__(
        self,
        server_host: str,
        server_port: int,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(max_retries, retry_delay)
        self.server_host: str   = server_host
        self.server_port: int   = server_port

    # --------------------------------------------------------------------------------
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_connection(self.server_host, self.server_port)


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
