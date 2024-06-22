import uuid
import random

from pydantic import BaseModel as PydanticBaseModel

from ecosystem import endpoint
from ecosystem.state_keepers import StatisticsKeeper

from ..dtos import RollDXRequestDto, RollDXResponseDto


@endpoint("roll", RollDXRequestDto)
async def roll_the_dice(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    StatisticsKeeper().increment("log.this.statistic")
    numbers = list(range(1, request.sides))
    return RollDXResponseDto(result = random.choice(numbers))
