import uuid
import random

from typing import List
from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests import HandlerBase

from ..dtos import GuessANumberResponseDto


# --------------------------------------------------------------------------------
class GuessANumber(HandlerBase):
    def __init__(self) -> None:
        super().__init__(
            "guess",
            "generates a funky number from a list"
        )

        self.numbers: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    async def run(self, request_uuid: uuid.UUID, request) -> PydanticBaseModel:
        return GuessANumberResponseDto(number = random.choice(self.numbers))
