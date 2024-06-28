import uuid
import random

from pydantic import BaseModel as PydanticBaseModel

from ecosystem import endpoint

from ..dtos import RollDXRequestDto, RollDXResponseDto


@endpoint("roll", RollDXRequestDto)
async def roll_the_dice(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    numbers = list(range(1, request.sides))
    return RollDXResponseDto(result = random.choice(numbers))
