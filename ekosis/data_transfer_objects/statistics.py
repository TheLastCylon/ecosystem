from typing import Any
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class StatsRequestDto(PydanticBaseModel):
    type: str


# --------------------------------------------------------------------------------
class StatsResponseDto(PydanticBaseModel):
    statistics: Any
