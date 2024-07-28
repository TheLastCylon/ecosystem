import uuid
import logging

from typing import cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..logs import EcoLogger
from ..data_transfer_objects import (
    LogLevelRequestDto,
    LogLevelResponseDto,
    LogBufferRequestDto,
    LogBufferResponseDto
)

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("eco.log.level", LogLevelRequestDto)
async def eco_log_level(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data   = cast(LogLevelRequestDto, request)
    logger = EcoLogger()
    logger.set_level(data.level)
    return LogLevelResponseDto(level=data.level)

# --------------------------------------------------------------------------------
@endpoint("eco.log.buffer", LogBufferRequestDto)
async def eco_log_buffer(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data   = cast(LogBufferRequestDto, request)
    logger = EcoLogger()
    logger.set_buffer_size(data.size)
    log.info(f"eco_log_buffer {data.size}")
    return LogBufferResponseDto(size=data.size)
