import datetime
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.data_transfer_objects import SpanKey

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
async def get_time(span_key : SpanKey) -> PydanticBaseModel:
    log.info(f"RCV: span_key[{span_key}]")
    week_day = week_days[datetime.datetime.today().weekday()]
    return CurrentTimeResponseDto(time=f"{week_day} {datetime.datetime.now()}")
