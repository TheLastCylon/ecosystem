import logging
import random

from typing import List
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint

from ..dtos import GuessResponseDto

logger = logging.getLogger()

@endpoint("dice_roller.guess")
async def dice_roller_guess(**kwargs) -> PydanticBaseModel:
    numbers: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return GuessResponseDto(number = random.choice(numbers))
