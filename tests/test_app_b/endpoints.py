import uuid
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.requests.queued_endpoint import queued_endpoint

from ..dtos.dtos import AppRequestDto, AppResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.b.endpoint", AppRequestDto)
async def app_b_endpoint(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=request.message)

# --------------------------------------------------------------------------------
@queued_endpoint("app.b.queued_endpoint", AppRequestDto)
async def app_b_queued_endpoint(request_uuid: uuid.UUID, request: AppRequestDto) -> bool:
    return True

# --------------------------------------------------------------------------------
@queued_endpoint("app.b.queued_endpoint_fail", AppRequestDto)
async def app_b_queued_endpoint_fail(request_uuid: uuid.UUID, request: AppRequestDto) -> bool:
    return False
