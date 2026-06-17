import logging

from ekosis.requests.buffered_endpoint import buffered_endpoint
from ekosis.data_transfer_objects import SpanKey

from .dtos import TrackerLogRequestDto
from .database import LogDatabase

log          = logging.getLogger()
log_database = LogDatabase()


@buffered_endpoint("app.log_request", TrackerLogRequestDto, page_size = 1000)
async def log_request(span_key : SpanKey, dto: TrackerLogRequestDto, **kwargs) -> bool:
    log.info(f"REQUEST : span_key[{span_key}], time[{dto.timestamp}], data[{dto.request}]")
    log_database.log_request(span_key, dto.request, dto.timestamp)
    return True


@buffered_endpoint("app.log_response", TrackerLogRequestDto, page_size = 1000)
async def log_response(span_key : SpanKey, dto: TrackerLogRequestDto, **kwargs) -> bool:
    log.info(f"RESPONSE: span_key[{span_key}], time[{dto.timestamp}], data[{dto.request}]")
    log_database.log_response(span_key, dto.request, dto.timestamp)
    return True
