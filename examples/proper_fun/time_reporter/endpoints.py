import uuid
import datetime
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint

from .dtos import CurrentTimeResponseDto

log = logging.getLogger()

week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --------------------------------------------------------------------------------
@endpoint("app.get_time")
async def get_time(uid: uuid.UUID, dto) -> PydanticBaseModel:
    log.info(f"RCV: request_uuid[{uid}]")
    week_day = week_days[datetime.datetime.today().weekday()]
    return CurrentTimeResponseDto(time=f"{week_day} {datetime.datetime.now()}")
