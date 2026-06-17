import logging
import time

from typing import List
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.util.fire_and_forget_tasks import run_soon
from ekosis.data_transfer_objects import SpanKey

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
async def _get_fortune(span_key : SpanKey) -> str:
    return (await get_fortune(span_key=span_key)).fortune


# --------------------------------------------------------------------------------
async def _get_joke(span_key : SpanKey) -> str:
    return (await get_joke(span_key=span_key)).joke


# --------------------------------------------------------------------------------
async def _get_lotto(span_key : SpanKey, request_data: List[str]) -> str:
    if len(request_data) > 1 and is_number(request_data[1]):
        how_many = int(request_data[1])
    else:
        how_many = 1
    return list_to_string(
        (await pick_numbers(how_many, span_key=span_key)).numbers
    )


# --------------------------------------------------------------------------------
async def _get_time(span_key : SpanKey) -> str:
    return (await get_time(span_key=span_key)).time


# --------------------------------------------------------------------------------
async def _get_prediction(span_key : SpanKey, question: str) -> str:
    return (await get_prediction(question, span_key=span_key)).prediction


# --------------------------------------------------------------------------------
@run_soon
async def _log_request(span_key : SpanKey, data: str, timestamp: float):
    await log_request(data, timestamp, span_key=span_key)


# --------------------------------------------------------------------------------
@run_soon
async def _log_response(span_key : SpanKey, data: str, timestamp: float):
    await log_response(data, timestamp, span_key=span_key)


# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(span_key : SpanKey, dto: RouterRequestDto) -> PydanticBaseModel:
    _log_request(span_key, dto.request, time.time())
    log.info(f"RCV: span_key[{span_key}]")
    request_data = dto.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(span_key)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(span_key)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(span_key, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(span_key)
    else:
        response = await _get_prediction(span_key, dto.request)

    log.info(f"RSP: span_key[{span_key}]")
    _log_response(span_key, response, time.time())
    return RouterResponseDto(response=response)
