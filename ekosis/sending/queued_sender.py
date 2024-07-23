from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from .queued_sender_class import QueuedSenderClass

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto
from ..state_keepers.queued_sender_keeper import QueuedSenderKeeper

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
def queued_sender(
    client           : ClientBase,
    route_key        : str,
    request_dto_type : Type[_RequestDTOType],
    response_dto_type: Type[_ResponseDTOType] = EmptyDto,
    wait_period      : float                  = 0,
    page_size        : int                    = 100,
    max_retries      : int                    = 0,
):
    def inner_decorator(function):
        queued_sender_keeper   = QueuedSenderKeeper()
        queued_sender_instance = QueuedSenderClass[_RequestDTOType, _ResponseDTOType](
            client,
            route_key,
            request_dto_type,
            response_dto_type,
            wait_period,
            page_size,
            max_retries
        )
        queued_sender_keeper.add_queued_sender(queued_sender_instance)

        async def wrapper(*args, **kwargs):
            request_uid_to_use = None
            if "request_uid" in kwargs.keys():
                request_uid_to_use = kwargs["request_uid"]

            await queued_sender_instance.push_message(await function(*args, **kwargs), request_uid_to_use)
        return wrapper
    return inner_decorator
