from typing import Dict, List, Any
from pydantic import BaseModel as PydanticBaseModel

# --------------------------------------------------------------------------------
class ErrorsResponseDto(PydanticBaseModel):
    errors: List[Dict[str, Any]]

# --------------------------------------------------------------------------------
class ErrorCleanerRequestDto(PydanticBaseModel):
    error_id: str
    count   : int
