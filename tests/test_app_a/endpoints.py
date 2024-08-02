import uuid
import logging

from typing import cast
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
# from ekosis.requests.queued_endpoint import queued_endpoint

from ..dtos.dtos import AppRequestDto, AppResponseDto
from .senders import test_pass_through_sender, test_queued_endpoint_sender, test_queued_sender_sender

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.test_endpoint", AppRequestDto)
async def test_endpoint(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=request.message)

# --------------------------------------------------------------------------------
@endpoint("app.test_pass_through", AppRequestDto)
async def test_pass_through(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    return cast(
        AppResponseDto,
        await test_pass_through_sender(request.message)
    )

# --------------------------------------------------------------------------------
@endpoint("app.test_queued_pass_through", AppRequestDto)
async def test_queued_pass_through(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    await test_queued_endpoint_sender(request.message)
    return AppResponseDto(message=request.message)

# --------------------------------------------------------------------------------
@endpoint("app.test_queued_sender", AppRequestDto)
async def test_queued_sender(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    await test_queued_sender_sender(request.message)
    return AppResponseDto(message=request.message)
