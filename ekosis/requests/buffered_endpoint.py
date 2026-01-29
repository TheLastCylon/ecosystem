from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from .request_router import RequestRouter
from .buffered_handler import BufferedHandler

from ..state_keepers.buffered_handler_keeper import BufferedHandlerKeeper
from ..data_transfer_objects import EmptyDto

_T = TypeVar("_T", bound=PydanticBaseModel)


def buffered_endpoint(
    route_key       : str,
    request_dto_type: Type[_T] = EmptyDto,
    page_size       : int = 100,
    max_retries     : int = 0,
):
    def inner_decorator(function):
        router                  = RequestRouter()
        buffered_handler_keeper = BufferedHandlerKeeper()

        new_handler = BufferedHandler[_T](
            route_key,
            function,
            request_dto_type,
            page_size,
            max_retries
        )
        router.register_handler(new_handler)
        buffered_handler_keeper.add_buffered_handler(new_handler)
        return function
    return inner_decorator
