import logging
from typing import Type
from pydantic import BaseModel as PydanticBaseModel
from .handler_base import HandlerBase

# --------------------------------------------------------------------------------
class StandardHandler(HandlerBase):
    _logger: logging.Logger   = logging.getLogger()

    def __init__(
        self,
        route_key: str,
        function,
        request_dto_type   : Type[PydanticBaseModel],
        accepted_parameters: set[str]
    ):
        super().__init__(route_key, request_dto_type, accepted_parameters)
        self.function = function

    async def run(self, **kwargs) -> PydanticBaseModel:
        call_kwargs = {k: v for k, v in kwargs.items() if k in self._accepted_params}
        return await self.function(**call_kwargs)
