from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class FortuneResponseDto(PydanticBaseModel):
    fortune: str
