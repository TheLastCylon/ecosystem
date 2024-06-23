import uuid
import json
import asyncio

from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from ..data_transfer_objects import RequestDTO, ResponseDTO, EmptyDto


# --------------------------------------------------------------------------------
class ClientBase(ABC):
    max_retries: int   = 3
    retry_delay: float = 0.1
    retry_count: int   = 0
    success    : bool  = False

    def __init__(
        self,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        self.success     = False

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def _send_message_retry_loop(self, request: str) -> str:
        pass

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto,
        request_uid      : uuid.UUID               = None
    ) -> PydanticBaseModel:
        if not request_uid:
            uuid_to_use = uuid.uuid4()
        else:
            uuid_to_use = request_uid

        self.success     = False
        self.retry_count = 0
        request          = RequestDTO(uid=str(uuid_to_use), route_key = route_key, data = data)
        request_str      = request.json()
        response_str     = await asyncio.create_task(self._send_message_retry_loop(f"{request_str}\n"))
        response_dict    = json.loads(response_str)
        response         = ResponseDTO(**response_dict)
        response_dto     = response_dto_type(**response.data)
        return response_dto
