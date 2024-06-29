import uuid
import random

from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests import endpoint

from ..dtos import RollRequestDto, RollResponseDto


@endpoint("dice_roller.roll", RollRequestDto)
async def dice_roller_roll(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    numbers = list(range(1, request.sides))
    return RollResponseDto(result = random.choice(numbers))
