import uuid

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Type

from ..data_transfer_objects import EmptyDto


# --------------------------------------------------------------------------------
class HandlerBase(ABC):
    def __init__(self, route_key: str, request_dto_type: Type[PydanticBaseModel] = EmptyDto):
        self._route_key      : str                     = route_key
        self.request_dto_type: Type[PydanticBaseModel] = request_dto_type

    def get_route_key(self) -> str:
        return self._route_key

    async def attempt_request(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        request_data = self.request_dto_type(**request_data)
        return await self.run(request_uuid, request_data)

    @abstractmethod
    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        pass


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
