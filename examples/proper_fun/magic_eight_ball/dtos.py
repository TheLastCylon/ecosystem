from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class Magic8BallRequestDto(PydanticBaseModel):
    question: str

# --------------------------------------------------------------------------------
class Magic8BallResponseDto(PydanticBaseModel):
    prediction: str
