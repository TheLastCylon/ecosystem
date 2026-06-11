from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class CurrentTimeResponseDto(PydanticBaseModel):
    time: str
