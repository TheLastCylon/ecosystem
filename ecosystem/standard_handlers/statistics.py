import uuid
from typing import Dict, Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests import HandlerBase


# --------------------------------------------------------------------------------
class StatisticsRequestDto(PydanticBaseModel):
    type: str


# --------------------------------------------------------------------------------
class StatisticsResponseDto(PydanticBaseModel):
    statistics: Dict[str, Any]


# --------------------------------------------------------------------------------
class Statistics(HandlerBase):
    def __init__(self):
        super(Statistics, self).__init__(
            "eco-statistics",
            "retrieves the application statistics",
            StatisticsRequestDto
        )

    async def run(self, request_uuid: uuid.UUID, request) -> PydanticBaseModel:
        request = cast(StatisticsRequestDto, request)

        if request.type == "current":
            stats = await self.statistics_keeper.get_current_statistics()
        elif request.type == "full":
            stats = await self.statistics_keeper.get_full_gathered_statistics()
        else:
            stats = await self.statistics_keeper.get_last_gathered_statistics()

        return StatisticsResponseDto(statistics=stats)


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
