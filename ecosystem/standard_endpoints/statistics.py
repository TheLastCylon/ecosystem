import uuid
from typing import Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests import endpoint
from ..state_keepers.statistics_keeper import StatisticsKeeper


# --------------------------------------------------------------------------------
class StatsRequestDto(PydanticBaseModel):
    type: str


# --------------------------------------------------------------------------------
class StatsResponseDto(PydanticBaseModel):
    statistics: Any


# --------------------------------------------------------------------------------
@endpoint("eco.statistics.get", StatsRequestDto)
async def eco_statistics_get(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    data         = cast(StatsRequestDto, request)
    stats_keeper = StatisticsKeeper()

    if data.type == "current":
        stats = await stats_keeper.get_current_statistics()
    elif data.type == "full":
        stats = await stats_keeper.get_full_gathered_statistics()
    else:
        stats = await stats_keeper.get_last_gathered_statistics()

    return StatsResponseDto(statistics=stats)
