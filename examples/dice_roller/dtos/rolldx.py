from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollDXRequestDto(PydanticBaseModel):
    sides: int


class RollDXResponseDto(PydanticBaseModel):
    result: int

