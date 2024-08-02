import asyncio
import socket
import uuid

from typing import Type, Tuple
from pydantic import BaseModel as PydanticBaseModel

from ..stream_client_base import StreamClientBase

from ...data_transfer_objects import EmptyDto

# --------------------------------------------------------------------------------
class TransientUDSClient(StreamClientBase):
    def __init__(
        self,
        server_path: str,
        timeout    : float = 5,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(timeout, max_retries, retry_delay)
        self.server_path : str  = server_path
        self.can_transmit: bool = hasattr(socket, "AF_UNIX")

    # --------------------------------------------------------------------------------
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_unix_connection(self.server_path)

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto,
        request_uid      : uuid.UUID               = None,
    ) -> PydanticBaseModel:
        if not self.can_transmit:
            raise Exception("UDS communications are not supported on this platform. Will not send message.")

        return await super().send_message(route_key, data, response_dto_type, request_uid)
