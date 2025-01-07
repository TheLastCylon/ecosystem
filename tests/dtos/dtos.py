from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class AppRequestDto(PydanticBaseModel):
    message: str

# --------------------------------------------------------------------------------
class AppResponseDto(PydanticBaseModel):
    message: str

# --------------------------------------------------------------------------------
class AppMiddlewareTestRequestDto(PydanticBaseModel):
    message       : str
    before_routing: bool = False
    after_routing : bool = False

# --------------------------------------------------------------------------------
class AppMiddlewareTestResponseDto(PydanticBaseModel):
    message       : str
    before_routing: bool = False
    after_routing : bool = False
