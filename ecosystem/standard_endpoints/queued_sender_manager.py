import uuid

from typing import Any, Dict, cast, List
from pydantic import BaseModel as PydanticBaseModel

from ..requests import endpoint
from ..state_keepers.queued_sender_keeper import QueuedSenderKeeper
from ..util.utility_functions import string_to_uuid


# --------------------------------------------------------------------------------
class QueuedSenderManagerRequestDto(PydanticBaseModel):
    queue_route_key: str


# --------------------------------------------------------------------------------
class ErrorQueueItemRequestDto(PydanticBaseModel):
    queue_route_key: str
    request_uid    : str


# --------------------------------------------------------------------------------
class QueuedSenderDatabaseSizesDto(PydanticBaseModel):
    send : int
    retry: int
    error: int


# --------------------------------------------------------------------------------
class QueuedSenderInformationDto(PydanticBaseModel):
    route_key           : str
    send_process_paused : bool
    retry_process_paused: bool
    database_sizes      : QueuedSenderDatabaseSizesDto


# --------------------------------------------------------------------------------
class QueuedSenderManagerResponseDto(PydanticBaseModel):
    queue_data  : QueuedSenderInformationDto | List[str] | None = None
    request_data: Any | None                                    = None
    message     : str


# --------------------------------------------------------------------------------
def make_queued_sender_information_dto(route_key: str, queue_info_dict: Dict[str, Any]) -> QueuedSenderInformationDto:
    return QueuedSenderInformationDto(
        route_key            = route_key,
        send_process_paused  = queue_info_dict["send_process_paused"],
        retry_process_paused = queue_info_dict["retry_process_paused"],
        database_sizes       = QueuedSenderDatabaseSizesDto(
            send  = queue_info_dict["sizes"]["send"],
            retry = queue_info_dict["sizes"]["retry"],
            error = queue_info_dict["sizes"]["error"]
        )
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.data", QueuedSenderManagerRequestDto)
async def eco_queued_sender_data(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.get_queue_information(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = None,
        message      = f"Queued Sender[{data.queue_route_key}]: Data retrieved."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.send_process.pause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_send_process_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.pause_send_process(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Paused SEND PROCESS."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.send_process.unpause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_send_process_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.un_pause_send_process(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: UN-Paused SEND PROCESS."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.retry_process.pause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_retry_process_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.pause_retry_process(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Paused RETRY PROCESS."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.retry_process.unpause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_retry_process_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.un_pause_retry_process(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: UN-Paused RETRY PROCESS."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.all.pause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_all_pause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.pause_all(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Paused ALL."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.all.unpause", QueuedSenderManagerRequestDto)
async def eco_queued_sender_all_unpause(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                  = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict       = await queued_sender_keeper.un_pause_all(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: UN-Paused ALL."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.get_first_10", QueuedSenderManagerRequestDto)
async def eco_queued_sender_errors_get_first_10(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    uuid_list            = await queued_sender_keeper.get_first_10_uuids(data.queue_route_key)
    if uuid_list is None:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = uuid_list,
        message    = f"Queued Sender[{data.queue_route_key}]: Retrieved first 10 UUIDs for error database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.reprocess.all", QueuedSenderManagerRequestDto)
async def eco_queued_sender_errors_reprocess_all(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.reprocess_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Error database entries, moved to Retry database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.clear", QueuedSenderManagerRequestDto)
async def eco_queued_sender_errors_clear(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(QueuedSenderManagerRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    queue_info_dict      = await queued_sender_keeper.clear_error_queue(data.queue_route_key)
    if not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        message    = f"Queued Sender[{data.queue_route_key}]: Error database cleared."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.reprocess.one", ErrorQueueItemRequestDto)
async def eco_queued_sender_errors_reprocess_one(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(ErrorQueueItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedSenderManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.reprocess_error_queue_request_uid(data.queue_route_key, uuid.UUID(data.request_uid))

    if queue_info_dict is None:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: Error database entry[{data.request_uid}] moved to Retry database."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.pop_request", ErrorQueueItemRequestDto)
async def eco_queued_sender_errors_pop_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(ErrorQueueItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedSenderManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.pop_request(data.queue_route_key, uuid.UUID(data.request_uid))
    if queue_info_dict is None:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: POPPED Error database entry[{data.request_uid}]."
    )


# --------------------------------------------------------------------------------
@endpoint("eco.queued_sender.errors.inspect_request", ErrorQueueItemRequestDto)
async def eco_queued_sender_errors_inspect_request(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data                 = cast(ErrorQueueItemRequestDto, request)
    queued_sender_keeper = QueuedSenderKeeper()
    request_uid          = string_to_uuid(data.request_uid)
    if not request_uid:
        return QueuedSenderManagerResponseDto(message=f"[{data.request_uid}] is not a valid UUID.")

    queue_info_dict = await queued_sender_keeper.inspect_request(data.queue_route_key, uuid.UUID(data.request_uid))
    if queue_info_dict is None:
        return QueuedSenderManagerResponseDto(message=f"No queued sender with route key: [{data.queue_route_key}]")
    elif not queue_info_dict:
        return QueuedSenderManagerResponseDto(message=f"No request with uid [{data.request_uid}] in queued sender error database, for route key: [{data.queue_route_key}]")

    return QueuedSenderManagerResponseDto(
        queue_data   = make_queued_sender_information_dto(data.queue_route_key, queue_info_dict),
        request_data = queue_info_dict["request_data"],
        message      = f"Queued Sender[{data.queue_route_key}]: INSPECTING Error database entry[{data.request_uid}]."
    )
