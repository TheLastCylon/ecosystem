from abc import ABC, abstractmethod
from pydantic import BaseModel as PydanticBaseModel

from ..data_transfer_objects import ResponseDTO


# --------------------------------------------------------------------------------
class ClientBase(ABC):
    @abstractmethod
    async def send_message(self, route_key: str, data: PydanticBaseModel) -> ResponseDTO:
        pass
