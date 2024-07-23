import uuid

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class SenderBase(Generic[_RequestDTOType, _ResponseDTOType], ABC):
    def __init__(
        self,
        client           : ClientBase,
        route_key        : str,
        request_dto_type : Type[_RequestDTOType],
        response_dto_type: Type[_ResponseDTOType] = EmptyDto,
    ):
        self._client           : ClientBase             = client
        self._route_key        : str                    = route_key
        self._request_dto_type : Type[_RequestDTOType]  = request_dto_type
        self._response_dto_type: Type[_ResponseDTOType] = response_dto_type

    def get_route_key(self) -> str:
        return self._route_key

    @abstractmethod
    async def send(self, *args, **kwargs):
        pass

    async def send_data(self, data: _RequestDTOType, request_uid: uuid.UUID = None) -> _ResponseDTOType:
        return await self._client.send_message(
            self._route_key,
            data,
            self._response_dto_type,
            request_uid
        )
