import uuid

from typing import Type, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel

from .queued_sender_base import QueuedSenderBase

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


class QueuedSenderClass(Generic[_RequestDTOType, _ResponseDTOType], QueuedSenderBase[_RequestDTOType, _ResponseDTOType]):
    def __init__(
        self,
        client           : ClientBase,
        route_key        : str,
        request_dto_type : Type[_RequestDTOType],
        response_dto_type: Type[_ResponseDTOType] = EmptyDto,
        wait_period      : float                  = 0,
        page_size        : int                    = 100,
        max_retries      : int                    = 0,
    ):
        super().__init__(
            client,
            route_key,
            request_dto_type,
            response_dto_type,
            wait_period,
            page_size,
            max_retries
        )

    async def push_message(self, message: _RequestDTOType, request_uuid: uuid.UUID = None):
        await self.enqueue(message, request_uuid)
