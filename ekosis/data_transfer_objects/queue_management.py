from typing import Any, List
from pydantic import BaseModel as PydanticBaseModel
from .json_protocol import SpanKey

# --------------------------------------------------------------------------------
class QManagementRequestDto(PydanticBaseModel):
    queue_route_key: str

# --------------------------------------------------------------------------------
class QManagementItemRequestDto(QManagementRequestDto):
    span_key: SpanKey

# --------------------------------------------------------------------------------
class QDatabaseSizesDto(PydanticBaseModel):
    pending: int
    error  : int


# --------------------------------------------------------------------------------
class BufferedEndpointInformationDto(PydanticBaseModel):
    route_key        : str
    receiving_paused : bool
    processing_paused: bool
    database_sizes   : QDatabaseSizesDto

# --------------------------------------------------------------------------------
class BufferedSenderInformationDto(PydanticBaseModel):
    route_key           : str
    send_process_paused : bool
    database_sizes      : QDatabaseSizesDto

# --------------------------------------------------------------------------------
class QManagementResponseDto(PydanticBaseModel):
    queue_data  : BufferedEndpointInformationDto | BufferedSenderInformationDto | List[str] | None = None
    request_data: Any | None = None
    message     : str
