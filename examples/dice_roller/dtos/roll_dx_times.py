from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollDXTimesRequestDto(PydanticBaseModel):
    sides   : int
    how_many: int
