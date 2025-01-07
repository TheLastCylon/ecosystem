import uuid

from typing import Any, Dict
from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..state_keepers.queued_handler_keeper import QueuedHandlerKeeper
from ..util.utility_functions import string_to_uuid
from ..data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementItemRequestDto,
    QDatabaseSizesDto,
    QueuedEndpointInformationDto,
    QManagementResponseDto
)

# --------------------------------------------------------------------------------
def make_queued_endpoint_information_dto(route_key: str, queue_info_dict: Dict[str, Any]) -> QueuedEndpointInformationDto:
    return QueuedEndpointInformationDto(
        route_key         = route_key,
        receiving_paused  = queue_info_dict["receiving_paused"],
        processing_paused = queue_info_dict["processing_paused"],
        database_sizes    = QDatabaseSizesDto(
            pending = queue_info_dict["pending"],
            error   = queue_info_dict["error"]
        )
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.data", QManagementRequestDto)
async def eco_queued_handler_data(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.get_queue_information(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        request_data = None,
        message      = f"Queued Endpoint[{dto.queue_route_key}]: Data retrieved.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.receiving.pause", QManagementRequestDto)
async def eco_queued_handler_receiving_pause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_receiving_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Paused RECEIVING.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.receiving.unpause", QManagementRequestDto)
async def eco_queued_handler_receiving_unpause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_receiving_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: UN-Paused RECEIVING.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.processing.pause", QManagementRequestDto)
async def eco_queued_handler_processing_pause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_processing_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Paused PROCESSING.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.processing.unpause", QManagementRequestDto)
async def eco_queued_handler_processing_unpause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_processing_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: UN-Paused PROCESSING.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.all.pause", QManagementRequestDto)
async def eco_queued_handler_all_pause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.pause_all_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Paused ALL.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.all.unpause", QManagementRequestDto)
async def eco_queued_handler_all_unpause(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.unpause_all_for_queued_handler(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: UN-Paused ALL.",
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.get_first_10", QManagementRequestDto)
async def eco_queued_handler_errors_get_first_10(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    uuid_list             = await queued_handler_keeper.get_first_10_error_uuids(dto.queue_route_key)
    if uuid_list is None:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = uuid_list,
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Retrieved first 10 UUIDs for error database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.reprocess.all", QManagementRequestDto)
async def eco_queued_handler_errors_reprocess_all(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.reprocess_error_queue(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Error database entries, moved to incoming database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.clear", QManagementRequestDto)
async def eco_queued_handler_errors_clear(dto: QManagementRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    queue_info_dict       = await queued_handler_keeper.clear_error_queue(dto.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        message    = f"Queued Endpoint[{dto.queue_route_key}]: Error database cleared."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.reprocess.one", QManagementItemRequestDto)
async def eco_queued_handler_errors_reprocess_one(dto: QManagementItemRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(dto.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{dto.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.reprocess_error_queue_request_uid(dto.queue_route_key, uuid.UUID(dto.request_uid))

    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{dto.request_uid}] in error queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{dto.queue_route_key}]: Error database entry[{dto.request_uid}] moved to incoming database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.pop_request", QManagementItemRequestDto)
async def eco_queued_handler_errors_pop_request(dto: QManagementItemRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(dto.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{dto.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.pop_request_from_error_queue(dto.queue_route_key, uuid.UUID(dto.request_uid))
    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{dto.request_uid}] in error queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{dto.queue_route_key}]: POPPED Error database entry[{dto.request_uid}]."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_handler.errors.inspect_request", QManagementItemRequestDto)
async def eco_queued_handler_errors_inspect_request(dto: QManagementItemRequestDto, **kwargs) -> PydanticBaseModel:
    queued_handler_keeper = QueuedHandlerKeeper()
    request_uid           = string_to_uuid(dto.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{dto.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_handler_keeper.inspect_request_from_error_queue(dto.queue_route_key, uuid.UUID(dto.request_uid))
    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queue for route key: [{dto.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{dto.request_uid}] in error queue for route key: [{dto.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_endpoint_information_dto(dto.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Endpoint[{dto.queue_route_key}]: INSPECTING Error database entry[{dto.request_uid}]."
    )
