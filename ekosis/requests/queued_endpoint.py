from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from .request_router import RequestRouter
from .queued_handler import QueuedHandler

from ..state_keepers.queued_handler_keeper import QueuedHandlerKeeper
from ..data_transfer_objects import EmptyDto

_T = TypeVar("_T", bound=PydanticBaseModel)


def queued_endpoint(
    route_key       : str,
    request_dto_type: Type[_T] = EmptyDto,
    page_size       : int = 100,
    max_retries     : int = 0,
):
    def inner_decorator(function):
        router                = RequestRouter()
        queued_handler_keeper = QueuedHandlerKeeper()

        new_handler = QueuedHandler[_T](
            route_key,
            function,
            request_dto_type,
            page_size,
            max_retries
        )
        router.register_handler(new_handler)
        queued_handler_keeper.add_queued_handler(new_handler)
        return function
    return inner_decorator
