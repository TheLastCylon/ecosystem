import uuid

from typing import Any, Dict, cast, List
from pydantic import BaseModel as PydanticBaseModel

from ..requests import endpoint
from ..state_keepers.queued_handler_keeper import QueuedHandlerKeeper
from ..util.utility_functions import string_to_uuid


# --------------------------------------------------------------------------------
class QueuedHandlerManagerRequestDto(PydanticBaseModel):
    queue_route_key: str


# --------------------------------------------------------------------------------
class ErrorQueueItemRequestDto(PydanticBaseModel):
    queue_route_key: str
    request_uid    : str


# --------------------------------------------------------------------------------
class QueuedEndpointDatabaseSizesDto(PydanticBaseModel):
    pending: int
    error  : int


# --------------------------------------------------------------------------------
class QueuedEndpointInformationDto(PydanticBaseModel):
    route_key        : str
    receiving_paused : bool
    processing_paused: bool
    database_sizes   : QueuedEndpointDatabaseSizesDto


# --------------------------------------------------------------------------------
class QueuedHandlerManagerResponseDto(PydanticBaseModel):
    queue_data  : QueuedEndpointInformationDto | List[str] | None = None
    request_data: Any | None                                      = None
    message     : str


# --------------------------------------------------------------------------------
def make_queued_endpoint_information_dto(route_key: str, queue_info_dict: Dict[str, Any]) -> QueuedEndpointInformationDto:
    return QueuedEndpointInformationDto(
        route_key         = route_key,
        receiving_paused  = queue_info_dict["receiving_paused"],
        processing_paused = queue_info_dict["processing_paused"],
        database_sizes    = QueuedEndpointDatabaseSizesDto(
            pending = queue_info_dict["pending"],
            error   = queue_info_dict["error"]
        )
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.data", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_data(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.get_queue_information(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(data=None, message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data   = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        request_data = None,
        message      = f"Queued Endpoint[{data.queue_route_key}]: Data retrieved.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.receiving.pause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_receiving_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_receiving_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: Paused RECEIVING.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.receiving.unpause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_receiving_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_receiving_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: UN-Paused RECEIVING.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.processing.pause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_processing_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_processing_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: Paused PROCESSING.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.processing.unpause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_processing_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_processing_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: UN-Paused PROCESSING.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.all.pause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_all_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_all_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: Paused ALL.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.all.unpause", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_all_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_all_for_queued_handler(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: UN-Paused ALL.",
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.get_first_10", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_errors_get_first_10(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    uuid_list             = await queued_handler_keeper.get_first_10_error_uuids(data.queue_route_key)
    if uuid_list is None:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = uuid_list,
        message    = f"Queued Endpoint[{data.queue_route_key}]: Retrieved first 10 UUIDs for error database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.reprocess.all", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_errors_reprocess_all(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.reprocess_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: Error database entries, moved to incoming database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.clear", QueuedHandlerManagerRequestDto)
async def eco_queued_handler_errors_clear(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedHandlerManagerRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.clear_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{data.queue_route_key}]: Error database cleared."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.reprocess.one", ErrorQueueItemRequestDto)
async def eco_queued_handler_errors_reprocess_one(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedHandlerManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.reprocess_error_queue_request_uid(data.queue_route_key, uuid.UUID(data.request_uid))

    if queue_info_dict is None:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data   = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{data.queue_route_key}]: Error database entry[{data.request_uid}] moved to incoming database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.pop_request", ErrorQueueItemRequestDto)
async def eco_queued_handler_errors_pop_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedHandlerManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.pop_request_from_error_queue(data.queue_route_key, uuid.UUID(data.request_uid))
    if queue_info_dict is None:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data   = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{data.queue_route_key}]: POPPED Error database entry[{data.request_uid}]."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.inspect_request", ErrorQueueItemRequestDto)
async def eco_queued_handler_errors_inspect_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(ErrorQueueItemRequestDto, request)
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedHandlerManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.inspect_request_from_error_queue(data.queue_route_key, uuid.UUID(data.request_uid))
    if queue_info_dict is None:
        return QueuedHandlerManagerResponseDto(message=f"No queue for route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedHandlerManagerResponseDto(message=f"No request with uid [{data.request_uid}] in error queue for route key: [{data.queue_route_key}]")

    return QueuedHandlerManagerResponseDto(
        queue_data   = make_queued_endpoint_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{data.queue_route_key}]: INSPECTING Error database entry[{data.request_uid}]."
    )
