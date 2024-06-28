from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from ..clients import ClientBase

_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


def sender(
    client           : ClientBase,
    route_key        : str,
    response_dto_type: Type[_ResponseDTOType]
):
    def inner_decorator(function):
        async def wrapper(*args, **kwargs) -> _ResponseDTOType:
            request_uid_to_use = None
            if "request_uid" in kwargs.keys():
                request_uid_to_use = kwargs["request_uid"]

            request_dto  = await function(*args, **kwargs)
            response_dto = await client.send_message(route_key, request_dto, response_dto_type, request_uid_to_use)
            return response_dto
        return wrapper
    return inner_decorator
