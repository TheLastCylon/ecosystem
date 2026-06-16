from pydantic import BaseModel as PydanticBaseModel
from .json_protocol import SpanKey

# --------------------------------------------------------------------------------
class BufferedEndpointResponseDTO(PydanticBaseModel):
    span_key: SpanKey
