from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from .request_router import RequestRouter
from .queued_handler import QueuedHandler

from ..data_transfer_objects import EmptyDto

_T = TypeVar("_T", bound=PydanticBaseModel)


def queued_endpoint(
    route_key       : str,
    request_dto_type: Type[_T] = EmptyDto,
    max_uncommited  : int = 0,
    max_retries     : int = 0,
):
    def inner_decorator(function):
        router      = RequestRouter()
        new_handler = QueuedHandler[_T](
            route_key,
            function,
            request_dto_type,
            max_uncommited,
            max_retries
        )
        router.register_handler(new_handler)
        return function
    return inner_decorator
