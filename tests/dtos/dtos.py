from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class AppRequestDto(PydanticBaseModel):
    message: str

# --------------------------------------------------------------------------------
class AppResponseDto(PydanticBaseModel):
    message: str
