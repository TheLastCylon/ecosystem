import uuid
import random

from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests import HandlerBase

from ..dtos import RollDXRequestDto, RollDXResponseDto


# ---------------------------------------------
class RollDX(HandlerBase):
    def __init__(self) -> None:
        super().__init__(
            "roll",
            "rolls a single dice, having a number of sides you specify",
            RollDXRequestDto
        )

    async def run(self, request_uuid: uuid.UUID, request) -> PydanticBaseModel:
        self.statistics_keeper.increment("log.this.statistic")
        numbers = list(range(1, request.sides))
        return RollDXResponseDto(result = random.choice(numbers))
