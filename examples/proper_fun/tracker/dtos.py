from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class TrackerLogRequestDto(PydanticBaseModel):
    request  : str
    timestamp: float
