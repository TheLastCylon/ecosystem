import uuid
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.requests.buffered_endpoint import buffered_endpoint

from ..dtos.dtos import AppRequestDto, AppResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.b.endpoint", AppRequestDto)
async def app_b_endpoint(uid: uuid.UUID, dto: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@buffered_endpoint("app.b.buffered_endpoint", AppRequestDto)
async def app_b_buffered_endpoint(uid: uuid.UUID, dto: AppRequestDto) -> bool:
    return True

# --------------------------------------------------------------------------------
@buffered_endpoint("app.b.buffered_endpoint_fail", AppRequestDto)
async def app_b_buffered_endpoint_fail(uid: uuid.UUID, dto: AppRequestDto) -> bool:
    return False
