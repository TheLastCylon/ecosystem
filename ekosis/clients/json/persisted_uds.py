import asyncio
import socket
import uuid

from typing import Type, Tuple
from pydantic import BaseModel as PydanticBaseModel

from ..persistent_stream_client_base import PersistentStreamClientBase

from ...data_transfer_objects import EmptyDto

# --------------------------------------------------------------------------------
class PersistedUDSClient(PersistentStreamClientBase):
    def __init__(
        self,
        server_path: str,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        self.server_path : str  = server_path
        self.can_transmit: bool = hasattr(socket, "AF_UNIX")
        super().__init__(max_retries, retry_delay)

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
