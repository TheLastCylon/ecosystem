import msgpack

from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from ..data_transfer_objects import (
    RequestDTO, ResponseDTO, EmptyDto, SpanKey,
    HEADER_LENGTH, pack_frame, parse_header, split_route_key_and_body,
)
from ..requests.status import Status

from ..exceptions import (
    ProtocolParsingException,
    ClientDeniedException,
    ValidationException,
    RouteKeyUnknownException,
    ServerBusyException,
    ProcessingException,
    UnhandledException,
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
    async def _send_message_retry_loop(self, request: bytes) -> bytes: # pragma: no cover
        pass

    # --------------------------------------------------------------------------------
    @staticmethod
    def generate_response_exception(request: ResponseDTO):
        if request.status == Status.PROTOCOL_PARSING_ERROR.value:
            return ProtocolParsingException(str(request.data))

        if request.status == Status.CLIENT_DENIED.value:
            return ClientDeniedException(str(request.data.json()))

        if request.status == Status.VALIDATION_ERROR.value:
            return ValidationException(str(request.data))

        if request.status == Status.ROUTE_KEY_UNKNOWN.value:
            return RouteKeyUnknownException(str(request.data))

        if request.status == Status.APPLICATION_BUSY.value:
            return ServerBusyException(str(request.data))

        if request.status == Status.PROCESSING_FAILURE.value:
            return ProcessingException(str(request.data))

        if request.status == Status.UNHANDLED.value:
            return UnhandledException(str(request.data))

        return UnknownStatusCodeException(f"Unrecognised status code[{request.status}]: {str(request.data)}")

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto,
        span_key         : SpanKey                 = None,
    ) -> PydanticBaseModel:
        span_key_to_use  = span_key if span_key else SpanKey.generate()
        self.success     = False
        self.retry_count = 0
        request_dto      = RequestDTO(span_key = span_key_to_use, route_key = route_key, data = data)
        request_body     = msgpack.packb(request_dto.model_dump(mode="json")["data"])
        request_frame    = pack_frame(request_dto.span_key, request_dto.route_key, request_body)

        response_frame   = await self._send_message_retry_loop(request_frame)

        response_span_key, route_key_len, total_len, _ = parse_header(response_frame[:HEADER_LENGTH])
        _, response_body = split_route_key_and_body(
            response_frame[HEADER_LENGTH:HEADER_LENGTH + total_len], route_key_len
        )
        response_dict    = msgpack.unpackb(response_body, raw=False)
        response         = ResponseDTO(span_key = response_span_key, **response_dict)

        if response.status != Status.SUCCESS.value:
            raise self.generate_response_exception(response)

        response_dto    = response_dto_type(**response.data)
        return response_dto
