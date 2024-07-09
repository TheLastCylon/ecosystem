import uuid
import logging

from ecosystem.requests import queued_endpoint

from .dtos import TrackerLogRequestDto
from .database import LogDatabase

log          = logging.getLogger()
log_database = LogDatabase()


@queued_endpoint("app.log_request", TrackerLogRequestDto, max_uncommited = 1000)
async def log_request(request_uuid: uuid.UUID, request: TrackerLogRequestDto) -> bool:
    log.info(f"REQUEST : uid[{request_uuid}], time[{request.timestamp}], data[{request.request}]")
    log_database.log_request(request_uuid, request.request, request.timestamp)
    return True


@queued_endpoint("app.log_response", TrackerLogRequestDto, max_uncommited = 1000)
async def log_response(request_uuid: uuid.UUID, request: TrackerLogRequestDto) -> bool:
    log.info(f"RESPONSE: uid[{request_uuid}], time[{request.timestamp}], data[{request.request}]")
    log_database.log_response(request_uuid, request.request, request.timestamp)
    return True
