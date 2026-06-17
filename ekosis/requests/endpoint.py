import inspect

from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from .request_router import RequestRouter
from .standard_handler import StandardHandler

from ..data_transfer_objects import EmptyDto

# --------------------------------------------------------------------------------
def endpoint(route_key: str, request_dto_type: Type[PydanticBaseModel] = EmptyDto):
    def inner_decorator(function):
        router              = RequestRouter()
        accepted_parameters = set(inspect.signature(function).parameters)
        new_handler         = StandardHandler(route_key, function, request_dto_type, accepted_parameters)
        router.register_handler(new_handler)
        return function
    return inner_decorator
