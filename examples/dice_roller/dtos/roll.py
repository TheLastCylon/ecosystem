from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollRequestDto(PydanticBaseModel):
    sides: int


# --------------------------------------------------------------------------------
class RollResponseDto(PydanticBaseModel):
    result: int
