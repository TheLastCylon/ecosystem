import uuid
import datetime
import logging

from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests.endpoint import endpoint

from .dtos import CurrentTimeResponseDto

log = logging.getLogger()

week_days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


@endpoint("app.get_time")
async def get_time(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    log.info(f"RCV: request_uuid[{request_uuid}]")
    week_day = week_days[datetime.datetime.today().weekday()]
    return CurrentTimeResponseDto(time=f"{week_day} {datetime.datetime.now()}")
