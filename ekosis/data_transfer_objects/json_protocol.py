from typing import Any
from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class RequestDTO(PydanticBaseModel):
    uid      : str
    route_key: str
    data     : Any

# --------------------------------------------------------------------------------
class ResponseDTO(PydanticBaseModel):
    uid   : str
    status: int
    data  : Any
