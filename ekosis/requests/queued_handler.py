import uuid

from typing import Type, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel
from .queued_handler_base import QueuedRequestHandlerBase

_T = TypeVar("_T", bound=PydanticBaseModel)


class QueuedHandler(Generic[_T], QueuedRequestHandlerBase[_T]):
    def __init__(
        self,
        route_key       : str,
        function,
        request_dto_type: Type[_T],
        page_size       : int = 100,
        max_retries     : int = 0,
    ):
        super().__init__(
            route_key,
            request_dto_type,
            page_size,
            max_retries
        )
        self.function = function

    # --------------------------------------------------------------------------------
    async def process_queued_request(self,  request_uuid: uuid.UUID, request: _T) -> bool:
        return await self.function(request_uuid, request)
