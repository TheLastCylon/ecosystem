import uuid
import logging
import random

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint

from ..dtos import RollRequestDto, RollResponseDto

logger = logging.getLogger()

@endpoint("dice_roller.roll", RollRequestDto)
async def dice_roller_roll(uid: uuid.UUID, dto: RollRequestDto) -> PydanticBaseModel:
    logger.debug(f"dice_roller_roll 000 [{dto}]")
    numbers = list(range(1, dto.sides))
    return RollResponseDto(result = random.choice(numbers))
