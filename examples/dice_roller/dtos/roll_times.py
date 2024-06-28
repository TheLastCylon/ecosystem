from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollTimesRequestDto(PydanticBaseModel):
    sides   : int
    how_many: int
