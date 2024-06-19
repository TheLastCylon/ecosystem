from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class GuessANumberResponseDto(PydanticBaseModel):
    number: int
