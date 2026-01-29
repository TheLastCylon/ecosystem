from typing import Type, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel
from .buffered_handler_base import BufferedRequestHandlerBase

_T = TypeVar("_T", bound=PydanticBaseModel)

class BufferedHandler(Generic[_T], BufferedRequestHandlerBase[_T]):
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
    async def process_buffered_request(self, **kwargs) -> bool:
        return await self.function(**kwargs)
