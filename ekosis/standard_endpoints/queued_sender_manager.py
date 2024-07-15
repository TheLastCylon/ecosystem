import uuid

from typing import Any, Dict, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..state_keepers.queued_sender_keeper import QueuedSenderKeeper
from ..util.utility_functions import string_to_uuid
from ..data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementItemRequestDto,
    QDatabaseSizesDto,
    QueuedSenderInformationDto,
    QManagementResponseDto
)

# --------------------------------------------------------------------------------
def make_queued_sender_information_dto(route_key: str, queue_info_dict: Dict[str, Any]) -> QueuedSenderInformationDto:
    return QueuedSenderInformationDto(
        route_key            = route_key,
        send_process_paused  = queue_info_dict["send_process_paused"],
        database_sizes       = QDatabaseSizesDto(
            pending = queue_info_dict["pending"],
            error   = queue_info_dict["error"]
        )
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.data", QManagementRequestDto)
async def eco_queued_sender_data(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.get_queue_information(data.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = None,
        message      = f"Queued Sender[{data.queue_route_key}]: Data retrieved."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.send_process.pause", QManagementRequestDto)
async def eco_queued_sender_send_process_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.pause_send_process(data.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Paused SEND PROCESS."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.send_process.unpause", QManagementRequestDto)
async def eco_queued_sender_send_process_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.un_pause_send_process(data.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: UN-Paused SEND PROCESS."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.get_first_10", QManagementRequestDto)
async def eco_queued_sender_errors_get_first_10(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    uuid_list            = await queued_sender_keeper.get_first_x_error_uuids(data.queue_route_key)
    if uuid_list is None:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = uuid_list,
        message    = f"Queued Sender[{data.queue_route_key}]: Retrieved first 10 UUIDs for error database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.reprocess.all", QManagementRequestDto)
async def eco_queued_sender_errors_reprocess_all(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.reprocess_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Error database entries, moved to Retry database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.clear", QManagementRequestDto)
async def eco_queued_sender_errors_clear(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.clear_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Error database cleared."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.reprocess.one", QManagementItemRequestDto)
async def eco_queued_sender_errors_reprocess_one(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.reprocess_error_queue_request_uid(data.queue_route_key, uuid.UUID(data.request_uid))

    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: Error database entry[{data.request_uid}] moved to Retry database."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.pop_request", QManagementItemRequestDto)
async def eco_queued_sender_errors_pop_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.pop_request_from_error_queue(data.queue_route_key, request_uid)
    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: POPPED Error database entry[{data.request_uid}]."
    )

# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.inspect_request", QManagementItemRequestDto)
async def eco_queued_sender_errors_inspect_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QManagementItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QManagementResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.inspect_request_in_error_queue(data.queue_route_key, uuid.UUID(data.request_uid))
    if queue_info_dict is None:
        return QManagementResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QManagementResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QManagementResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: INSPECTING Error database entry[{data.request_uid}]."
    )
