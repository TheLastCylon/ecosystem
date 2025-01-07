from abc import ABC
from pydantic import BaseModel as PydanticBaseModel
from ..data_transfer_objects import RequestDTO

class MiddlewareBase(ABC):
    async def before_routing(self, **kwargs) -> RequestDTO:
        return kwargs["protocol_dto"]

    async def after_routing(self, **kwargs) -> PydanticBaseModel:
        return kwargs["response_dto"]
