import logging

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Type

from ..data_transfer_objects import EmptyDto

# --------------------------------------------------------------------------------
class HandlerBase(ABC):
    _logger: logging.Logger   = logging.getLogger()

    def __init__(
        self,
        route_key: str,
        request_dto_type   : Type[PydanticBaseModel] = EmptyDto,
        accepted_parameters: set[str]                = set()
    ):
        self._route_key      : str                     = route_key
        self.request_dto_type: Type[PydanticBaseModel] = request_dto_type
        self._accepted_params: set[str]                = accepted_parameters

    def get_route_key(self) -> str:
        return self._route_key

    async def attempt_request(self, protocol_dto, **kwargs) -> PydanticBaseModel:
        kwargs["dto"] = self.request_dto_type(**protocol_dto.data)
        return await self.run(**kwargs)

    @abstractmethod
    async def run(self, **kwargs) -> PydanticBaseModel: # pragma: no cover
        pass
