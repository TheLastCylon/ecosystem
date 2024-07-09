import uuid
import logging
import time

from typing import cast, List
from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests import endpoint
from ecosystem.util.fire_and_forget_tasks import run_soon

from .dtos import RouterRequestDto, RouterResponseDto

from .senders import (
    get_fortune,
    get_joke,
    pick_numbers,
    get_prediction,
    get_time,
    log_request,
    log_response
)

log = logging.getLogger()


# --------------------------------------------------------------------------------
def list_to_string(strings: List[str]) -> str:
    result = ""
    for s in strings:
        result += f"{s}\n"
    return result


def is_number(string: str) -> bool:
    return string.lstrip('-').isdigit()


# --------------------------------------------------------------------------------
async def _get_fortune(uid: uuid.UUID) -> str:
    return (await get_fortune(request_uid=uid)).fortune


# --------------------------------------------------------------------------------
async def _get_joke(uid: uuid.UUID) -> str:
    return (await get_joke(request_uid=uid)).joke


# --------------------------------------------------------------------------------
async def _get_lotto(uid: uuid.UUID, request_data: List[str]) -> str:
    if len(request_data) > 1 and is_number(request_data[1]):
        how_many = int(request_data[1])
    else:
        how_many = 1
    return list_to_string(
        (await pick_numbers(how_many, request_uid=uid)).numbers
    )


# --------------------------------------------------------------------------------
async def _get_time(uid: uuid.UUID) -> str:
    return (await get_time(request_uid=uid)).time


# --------------------------------------------------------------------------------
async def _get_prediction(uid: uuid.UUID, question: str) -> str:
    return (await get_prediction(question, request_uid=uid)).prediction


# --------------------------------------------------------------------------------
@run_soon
async def _log_request(uid: uuid.UUID, data: str, timestamp: float):
    await log_request(data, timestamp, request_uid=uid)


# --------------------------------------------------------------------------------
@run_soon
async def _log_response(uid: uuid.UUID, data: str, timestamp: float):
    await log_response(data, timestamp, request_uid=uid)


# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    request_data_raw = cast(RouterRequestDto, request)
    _log_request(request_uuid, request_data_raw.request, time.time())
    log.info(f"RCV: request_uuid[{request_uuid}]")
    request_data = request_data_raw.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(request_uuid)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(request_uuid)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(request_uuid, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(request_uuid)
    else:
        response = await _get_prediction(request_uuid, request_data_raw.request)

    log.info(f"RSP: request_uuid[{request_uuid}]")
    _log_response(request_uuid, response, time.time())
    return RouterResponseDto(response=response)
