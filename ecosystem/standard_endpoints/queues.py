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
class ErrorQueueItemMessageResponseDto(PydanticBaseModel):
    action : str
    message: str


# --------------------------------------------------------------------------------
class QueuedHandlerManagerResponseDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
def string_to_uuid(value: str) -> uuid.UUID | bool:
    try:
        return uuid.UUID(value)
    except ValueError:
        return False


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-get-first-10", QueuedHandlerManagerRequestDto)
async def error_queue_get_first_10(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    uuid_list             = await queued_handler_keeper.get_first_10_error_uuids(data.queue_route_key)
    if not uuid_list:
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"{str(uuid_list)}")


# --------------------------------------------------------------------------------
@endpoint("eco-queue-size", QueuedHandlerManagerRequestDto)
async def queue_size(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_size_dict       = await queued_handler_keeper.get_queue_sizes(data.queue_route_key)
    if not queue_size_dict:
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"incoming:[{queue_size_dict['incoming']}] error:[{queue_size_dict['error']}]")


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
    if not request_uuid:
        return QueuedHandlerManagerResponseDto(message = f"[{data.request_uid}] is not a valid UUID.")

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
    if not request_uuid:
        return QueuedHandlerManagerResponseDto(message = f"[{data.request_uid}] is not a valid UUID.")

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
@endpoint("eco-error-queue-clear", QueuedHandlerManagerRequestDto)
async def error_queue_reprocess_all(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    await queued_handler_keeper.clear_error_queue(data.queue_route_key)

    return QueuedHandlerManagerResponseDto(message = f"Error queue for route key [{data.queue_route_key}] has been cleared.")


# --------------------------------------------------------------------------------
@endpoint("eco-error-queue-reprocess-request", ErrorQueueItemRequestDto)
async def error_queue_reprocess_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uuid          = string_to_uuid(data.request_uid)
    if not request_uuid:
        return QueuedHandlerManagerResponseDto(message = f"[{data.request_uid}] is not a valid UUID.")

    if not queued_handler_keeper.has_route_key(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    result = await queued_handler_keeper.reprocess_error_queue_request_uid(data.queue_route_key, uuid.UUID(data.request_uid))

    if not result:
        return QueuedHandlerManagerResponseDto(message = f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Request with uid [{data.request_uid}] in queue for route key [{data.queue_route_key}] now being reprocessed.")
