import uuid
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.requests.queued_endpoint import queued_endpoint

from ..dtos.dtos import AppRequestDto, AppResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.test_endpoint", AppRequestDto)
async def test_endpoint(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    return AppResponseDto(message=request.message)

# --------------------------------------------------------------------------------
@queued_endpoint("app.test_queued_endpoint", AppRequestDto)
async def log_request(request_uuid: uuid.UUID, request: AppRequestDto) -> bool:
    return True
