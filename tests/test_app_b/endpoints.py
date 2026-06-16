import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.requests.buffered_endpoint import buffered_endpoint
from ekosis.data_transfer_objects import SpanKey

from ..dtos.dtos import AppRequestDto, AppResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.b.endpoint", AppRequestDto)
async def app_b_endpoint(span_key: SpanKey, dto: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=dto.message)

# --------------------------------------------------------------------------------
@buffered_endpoint("app.b.buffered_endpoint", AppRequestDto)
async def app_b_buffered_endpoint(span_key: SpanKey, dto: AppRequestDto) -> bool:
    return True

# --------------------------------------------------------------------------------
@buffered_endpoint("app.b.buffered_endpoint_fail", AppRequestDto)
async def app_b_buffered_endpoint_fail(span_key: SpanKey, dto: AppRequestDto) -> bool:
    return False
