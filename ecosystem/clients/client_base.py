from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from ..data_transfer_objects import EmptyDto


# --------------------------------------------------------------------------------
class ClientBase(ABC):
    @abstractmethod
    async def send_message(
            self,
            route_key        : str,
            data             : PydanticBaseModel,
            response_dto_type: Type[PydanticBaseModel] = EmptyDto
    ) -> PydanticBaseModel:
        pass
