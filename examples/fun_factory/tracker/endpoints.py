import uuid
import logging

from ekosis.requests.queued_endpoint import queued_endpoint

from .dtos import TrackerLogRequestDto
from .database import LogDatabase

log          = logging.getLogger()
log_database = LogDatabase()


@queued_endpoint("app.log_request", TrackerLogRequestDto, page_size = 1000)
async def log_request(uid: uuid.UUID, dto: TrackerLogRequestDto, **kwargs) -> bool:
    log.info(f"REQUEST : uid[{uid}], time[{dto.timestamp}], data[{dto.request}]")
    log_database.log_request(uid, dto.request, dto.timestamp)
    return True


@queued_endpoint("app.log_response", TrackerLogRequestDto, page_size = 1000)
async def log_response(uid: uuid.UUID, dto: TrackerLogRequestDto, **kwargs) -> bool:
    log.info(f"RESPONSE: uid[{uid}], time[{dto.timestamp}], data[{dto.request}]")
    log_database.log_response(uid, dto.request, dto.timestamp)
    return True
