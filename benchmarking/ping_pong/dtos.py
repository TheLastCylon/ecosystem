from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class PingRequestDto(PydanticBaseModel):
    message: str

# --------------------------------------------------------------------------------
class PongResponseDto(PydanticBaseModel):
    message: str
