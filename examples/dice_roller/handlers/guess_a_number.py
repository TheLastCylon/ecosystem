import uuid
import random

from typing import List
from pydantic import BaseModel as PydanticBaseModel

from ecosystem import endpoint

from ..dtos import GuessANumberResponseDto


@endpoint("guess")
async def guess_a_number(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    numbers: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return GuessANumberResponseDto(number = random.choice(numbers))
