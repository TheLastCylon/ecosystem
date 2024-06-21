import uuid
from typing import Dict, Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests import endpoint
from ..state_keepers import QueuedHandlerKeeper


# --------------------------------------------------------------------------------
class QueuedHandlerManagerRequestDto(PydanticBaseModel):
    queue_route_key: str


# --------------------------------------------------------------------------------
class QueuedHandlerManagerResponseDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
@endpoint("eco-pause-queue-receiving", QueuedHandlerManagerRequestDto)
async def pause_queue_receiving(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.pause_receiving_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Paused RECEIVING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-unpause-queue-receiving", QueuedHandlerManagerRequestDto)
async def unpause_queue_receiving(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.unpause_receiving_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"UN-Paused RECEIVING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-pause-queue-processing", QueuedHandlerManagerRequestDto)
async def pause_queue_processing(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.pause_processing_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"Paused PROCESSING for queue with route key: [{data.queue_route_key}]")


# --------------------------------------------------------------------------------
@endpoint("eco-pause-queue-processing", QueuedHandlerManagerRequestDto)
async def unpause_queue_processing(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()

    if not queued_handler_keeper.unpause_processing_for_queued_handler(data.queue_route_key):
        return QueuedHandlerManagerResponseDto(message = f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(message = f"UN-Paused PROCESSING for queue with route key: [{data.queue_route_key}]")
