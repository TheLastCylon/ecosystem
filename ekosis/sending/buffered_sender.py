from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from .buffered_sender_class import BufferedSenderClass

from ..clients import MultiplexedTCPClient, MultiplexedUDSClient
from ..data_transfer_objects import EmptyDto
from ..state_keepers.buffered_sender_keeper import BufferedSenderKeeper

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
# BufferedSender needs a multiplexed persisted connection (UDP can't hold one,
# and a plain Persisted*Client serialises the whole round trip behind one
# permit) -- mirrors ekocpp's MultiplexedClient-constrained overloads on
# ApplicationBase::register_buffered_sender. Each decorated function gets its
# own freshly-built client -- never a caller-supplied, potentially-shared one.
# That sharing is exactly what caused ekocpp's SpanKey-collision bug when two
# BufferedSenders demuxed responses through the same client (see
# multiplexed_stream_client.md). Removing the client parameter here removes
# the shape that made the mistake possible on the Python side too. The client's
# start() is called later, from BufferedSenderBase.setup() -- not here, since
# this decorator runs at module-import time, before any event loop exists.
def _build_client(host: str, port: int, socket_path: str):
    if socket_path is not None:
        if host is not None or port is not None:
            raise ValueError("buffered_sender: pass either (host, port) or socket_path, not both.")
        return MultiplexedUDSClient(socket_path)

    if host is None or port is None:
        raise ValueError("buffered_sender: must pass either (host, port) or socket_path.")
    return MultiplexedTCPClient(host, port)


# --------------------------------------------------------------------------------
def buffered_sender(
    route_key        : str,
    request_dto_type : Type[_RequestDTOType],
    response_dto_type: Type[_ResponseDTOType] = EmptyDto,
    *,
    host             : str   = None,
    port             : int   = None,
    socket_path      : str   = None,
    wait_period      : float = 0,
    page_size        : int   = 100,
    max_retries      : int   = 0,
):
    def inner_decorator(function):
        client                   = _build_client(host, port, socket_path)
        buffered_sender_keeper   = BufferedSenderKeeper()
        buffered_sender_instance = BufferedSenderClass[_RequestDTOType, _ResponseDTOType](
            client,
            route_key,
            request_dto_type,
            response_dto_type,
            wait_period,
            page_size,
            max_retries
        )
        buffered_sender_keeper.add_buffered_sender(buffered_sender_instance)

        async def wrapper(*args, **kwargs):
            span_key_to_use = None
            if "span_key" in kwargs.keys():
                span_key_to_use = kwargs["span_key"]

            await buffered_sender_instance.push_message(await function(*args, **kwargs), span_key_to_use)
        return wrapper
    return inner_decorator
