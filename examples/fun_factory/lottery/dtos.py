from typing import List
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class NumberPickerRequestDto(PydanticBaseModel):
    how_many: int


# --------------------------------------------------------------------------------
class NumberPickerResponseDto(PydanticBaseModel):
    numbers: List[str]
