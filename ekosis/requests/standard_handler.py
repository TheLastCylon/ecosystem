import logging
from typing import Type
from pydantic import BaseModel as PydanticBaseModel
from .handler_base import HandlerBase


class StandardHandler(HandlerBase):
    _logger: logging.Logger   = logging.getLogger()

    def __init__(
        self,
        route_key: str,
        function,
        request_dto_type: Type[PydanticBaseModel]
    ):
        super().__init__(route_key, request_dto_type)
        self.function = function

    async def run(self, **kwargs) -> PydanticBaseModel:
        return await self.function(**kwargs)
