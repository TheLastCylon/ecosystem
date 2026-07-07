import asyncio
import socket

from typing import Type, Tuple
from pydantic import BaseModel as PydanticBaseModel

from .multiplexed_stream_client_base import MultiplexedStreamClientBase

from ..data_transfer_objects import EmptyDto, SpanKey

# --------------------------------------------------------------------------------
class MultiplexedUDSClient(MultiplexedStreamClientBase):
    def __init__(
        self,
        server_path                : str,
        timeout                    : float = 5,
        heartbeat_period           : float = 60,
        max_retries                : int   = 3,
        retry_delay                : float = 0.1,
        staleness_sweep_period     : float = 30,
        staleness_warning_threshold: float = 60,
    ):
        self.server_path : str  = server_path
        self.can_transmit: bool = hasattr(socket, "AF_UNIX")
        super().__init__(timeout, heartbeat_period, max_retries, retry_delay, staleness_sweep_period, staleness_warning_threshold)

    # --------------------------------------------------------------------------------
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.open_unix_connection(self.server_path)

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto,
        span_key         : SpanKey                 = None
    ) -> PydanticBaseModel:
        if not self.can_transmit:
            raise Exception("UDS communications are not supported on this platform. Will not send message.")

        return await super().send_message(route_key, data, response_dto_type, span_key)
