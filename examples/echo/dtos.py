from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class EchoRequestDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
class EchoResponseDto(PydanticBaseModel):
    message: str
