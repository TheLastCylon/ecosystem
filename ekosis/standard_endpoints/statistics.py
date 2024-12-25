from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..state_keepers.statistics_keeper import StatisticsKeeper
from ..data_transfer_objects import StatsRequestDto, StatsResponseDto

# --------------------------------------------------------------------------------
@endpoint("eco.statistics.get", StatsRequestDto)
async def eco_statistics_get(dto: StatsRequestDto, **kwargs) -> PydanticBaseModel:
    stats_keeper = StatisticsKeeper()

    if dto.type == "current":
        stats = await stats_keeper.get_current_statistics()
    elif dto.type == "full":
        stats = await stats_keeper.get_full_gathered_statistics()
    else:
        stats = await stats_keeper.get_last_gathered_statistics()

    return StatsResponseDto(statistics=stats)
