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
        max_uncommited   : int = 0,
        max_retries      : int = 0,
    ):
        super().__init__(
            client,
            route_key,
            request_dto_type,
            response_dto_type,
            max_uncommited,
            max_retries
        )

    async def push_message(self, message: _RequestDTOType):
        await self.enqueue(message)
