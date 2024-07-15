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


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
