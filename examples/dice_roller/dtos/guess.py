from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class GuessResponseDto(PydanticBaseModel):
    number: int
