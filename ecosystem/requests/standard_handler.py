import uuid
from typing import Type
from pydantic import BaseModel as PydanticBaseModel
from .handler_base import HandlerBase


class StandardHandler(HandlerBase):
    def __init__(
        self,
        route_key: str,
        function,
        request_dto_type: Type[PydanticBaseModel]
    ):
        super().__init__(route_key, request_dto_type)
        self.function = function

    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        return await self.function(request_uuid, request_data)
