import uuid
import logging

from typing import cast
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.util.fire_and_forget_tasks import run_soon
from ekosis.exceptions import ApplicationProcessingException

from ..dtos.dtos import AppRequestDto, AppResponseDto
from .senders import (
    app_a_sender_app_b_endpoint,
    app_a_sender_app_b_queued_endpoint,
    app_a_queued_sender_app_b_queued_endpoint,
    app_a_queued_sender_no_server
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.a.endpoint", AppRequestDto)
async def app_a_endpoint(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@endpoint("app.a.pass_through", AppRequestDto)
async def app_a_pass_through(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    return cast(
        AppResponseDto,
        await app_a_sender_app_b_endpoint(dto.message)
    )

# --------------------------------------------------------------------------------
@endpoint("app.a.queued_pass_through", AppRequestDto)
async def app_a_queued_pass_through(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    await app_a_sender_app_b_queued_endpoint(dto.message)
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@endpoint("app.a.queued_sender", AppRequestDto)
async def app_a_queued_sender(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    await app_a_queued_sender_app_b_queued_endpoint(dto.message)
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@run_soon
async def enqueue_no_such_server(uid: uuid.UUID, message: str):
    await app_a_queued_sender_no_server(message, request_uid=uid)

# --------------------------------------------------------------------------------
@endpoint("app.a.send_no_such_server", AppRequestDto)
async def app_a_send_no_such_server(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    enqueue_no_such_server(uid, dto.message)
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@endpoint("app.a.exception", AppRequestDto)
async def app_b_endpoint(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    raise RuntimeError("app.a.exception: RuntimeError")

# --------------------------------------------------------------------------------
@endpoint("app.a.exception1", AppRequestDto)
async def app_b_endpoint1(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    raise ApplicationProcessingException("app.a.exception: ProcessingException")
