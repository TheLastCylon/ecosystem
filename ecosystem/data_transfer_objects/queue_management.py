from typing import Any, List
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class QManagementRequestDto(PydanticBaseModel):
    queue_route_key: str


# --------------------------------------------------------------------------------
class QManagementItemRequestDto(QManagementRequestDto):
    request_uid    : str


# --------------------------------------------------------------------------------
class QDatabaseSizesDto(PydanticBaseModel):
    pending: int
    error  : int


# --------------------------------------------------------------------------------
class QueuedEndpointInformationDto(PydanticBaseModel):
    route_key        : str
    receiving_paused : bool
    processing_paused: bool
    database_sizes   : QDatabaseSizesDto


# --------------------------------------------------------------------------------
class QueuedSenderInformationDto(PydanticBaseModel):
    route_key           : str
    send_process_paused : bool
    database_sizes      : QDatabaseSizesDto


# --------------------------------------------------------------------------------
class QManagementResponseDto(PydanticBaseModel):
    queue_data  : QueuedEndpointInformationDto | QueuedSenderInformationDto | List[str] | None = None
    request_data: Any | None = None
    message     : str
