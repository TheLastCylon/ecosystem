from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class RouterRequestDto(PydanticBaseModel):
    request: str

# --------------------------------------------------------------------------------
class RouterResponseDto(PydanticBaseModel):
    response: str
