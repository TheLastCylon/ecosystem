import uuid
import logging

from typing import cast
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
# from ekosis.requests.queued_endpoint import queued_endpoint

from .dtos import AppRequestDto, AppResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.test_endpoint", AppRequestDto)
async def test_endpoint(request_uuid: uuid.UUID, request: AppRequestDto) -> PydanticBaseModel:
    data = cast(AppRequestDto, request)
    return AppResponseDto(message=data.message)

# --------------------------------------------------------------------------------
# @queued_endpoint("app.test_queued_endpoint", TestAppRequestDto)
# async def log_request(request_uuid: uuid.UUID, request: TestAppRequestDto) -> bool:
#     log.info(f"REQUEST : uid[{request_uuid}], time[{request.timestamp}], data[{request.request}]")
#     return True
