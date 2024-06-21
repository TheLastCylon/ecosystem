import uuid
from typing import Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests import endpoint
from ..state_keepers import QueuedHandlerKeeper


# --------------------------------------------------------------------------------
class QueuedHandlerManagerRequestDto(PydanticBaseModel):
    queue_route_key: str


# --------------------------------------------------------------------------------
class ErrorQueueItemRequestDto(PydanticBaseModel):
    queue_route_key: str
    request_uid    : str


# --------------------------------------------------------------------------------
class ErrorQueueItemResponseDto(PydanticBaseModel):
    action      : str
    request_data: Any


# --------------------------------------------------------------------------------
class QueuedHandlerManagerResponseDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
@endpoint("eco-queue-receiving-pause", QueuedHandlerManagerRequestDto)
async def queue_receiving_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.pause_receiving_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Paused RECEIVING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-queue-receiving-unpause", QueuedHandlerManagerRequestDto)
async def queue_receiving_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.unpause_receiving_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"UN-Paused RECEIVING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-queue-processing-pause", QueuedHandlerManagerRequestDto)
async def queue_processing_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.pause_processing_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Paused PROCESSING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-queue-processing-unpause", QueuedHandlerManagerRequestDto)
async def queue_processing_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.unpause_processing_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"UN-Paused PROCESSING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-pop-request", ErrorQueueItemRequestDto)
async def error_queue_pop_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    queued_request = await queued_handler_keeper.pop_request_from_error_queue(data.queue_route_key, uuid.UUID(data.request_uid))
    if not queued_request:
        return QueuedHandlerManagerResponseDto(message = f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return ErrorQueueItemResponseDto(
        action       = "POPPED",
        request_data = queued_request
    )


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-inspect-request", ErrorQueueItemRequestDto)
async def error_queue_inspect_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    queued_request = await queued_handler_keeper.inspect_request_from_error_queue(data.queue_route_key, uuid.UUID(data.request_uid))
    if not queued_request:
        return QueuedHandlerManagerResponseDto(message = f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return ErrorQueueItemResponseDto(
        action       = "INSPECTED",
        request_data = queued_request
    )


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-reprocess-all", QueuedHandlerManagerRequestDto)
async def error_queue_reprocess_all(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    await queued_handler_keeper.reprocess_error_queue(data.queue_route_key)

    return QueuedHandlerManagerResponseDto(message = f"Error queue for route key [{data.queue_route_key}] now being reprocessed.")


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-reprocess-request", ErrorQueueItemRequestDto)
async def error_queue_reprocess_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    result = await queued_handler_keeper.reprocess_error_queue_request_uid(data.queue_route_key, uuid.UUID(data.request_uid))

    if not result:
        return QueuedHandlerManagerResponseDto(message = f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Request with uid [{data.request_uid}] in queue for route key [{data.queue_route_key}] now being reprocessed.")
