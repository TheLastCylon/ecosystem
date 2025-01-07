import uuid
import logging

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
async def eco_log_level(dto: LogLevelRequestDto, **kwargs) -> PydanticBaseModel:
    logger = EcoLogger()
    logger.set_level(dto.level)
    return LogLevelResponseDto(level=dto.level)

# --------------------------------------------------------------------------------
@endpoint("eco.log.buffer", LogBufferRequestDto)
async def eco_log_buffer(dto: LogBufferRequestDto, **kwargs) -> PydanticBaseModel:
    logger = EcoLogger()
    logger.set_buffer_size(dto.size)
    log.info(f"eco_log_buffer {dto.size}")
    return LogBufferResponseDto(size=dto.size)
