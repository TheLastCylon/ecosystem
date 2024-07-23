import uuid
import json

from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from ..data_transfer_objects import RequestDTO, ResponseDTO, EmptyDto
from ..requests.status import Status

from ..exceptions import (
    ProtocolParsingException,
    ClientDeniedException,
    PydanticValidationException,
    RouteKeyUnknownException,
    ServerBusyException,
    ProcessingException,
    UnknownException,
    UnknownStatusCodeException,
)

# --------------------------------------------------------------------------------
class ClientBase(ABC):
    def __init__(
        self,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        self.max_retries: int   = max_retries
        self.retry_delay: float = retry_delay
        self.retry_count: int   = 0
        self.success    : bool  = False

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def _send_message_retry_loop(self, request: str) -> str:
        pass

    # --------------------------------------------------------------------------------
    @staticmethod
    def generate_response_exception(request: ResponseDTO):
        if request.status == Status.PROTOCOL_PARSING_ERROR.value:
            return ProtocolParsingException(str(request.data))

        if request.status == Status.CLIENT_DENIED.value:
            return ClientDeniedException(str(request.data.json()))

        if request.status == Status.PYDANTIC_VALIDATION_ERROR.value:
            return PydanticValidationException(str(request.data))

        if request.status == Status.ROUTE_KEY_UNKNOWN.value:
            return RouteKeyUnknownException(str(request.data))

        if request.status == Status.APPLICATION_BUSY.value:
            return ServerBusyException(str(request.data))

        if request.status == Status.PROCESSING_FAILURE.value:
            return ProcessingException(str(request.data))

        if request.status == Status.UNKNOWN.value:
            return UnknownException(str(request.data))

        return UnknownStatusCodeException(f"Unrecognised status code[{request.status}]: {str(request.data)}")

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto,
        request_uid      : uuid.UUID               = None
    ) -> PydanticBaseModel:
        if not request_uid:
            uuid_to_use = uuid.uuid4()
        else:
            uuid_to_use = request_uid

        self.success     = False
        self.retry_count = 0
        request          = RequestDTO(uid=str(uuid_to_use), route_key = route_key, data = data)
        request_str      = request.model_dump_json()
        response_str     = await self._send_message_retry_loop(f"{request_str}\n")
        response_dict    = json.loads(response_str)
        response         = ResponseDTO(**response_dict)

        if response.status != Status.SUCCESS.value:
            raise self.generate_response_exception(response)

        response_dto     = response_dto_type(**response.data)
        return response_dto
