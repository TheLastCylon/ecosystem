from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class JokerResponseDto(PydanticBaseModel):
    joke: str
