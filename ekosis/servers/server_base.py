import logging
import timeit

from typing import Any
from pydantic import ValidationError

from ..data_transfer_objects import RequestDTO, ResponseDTO, SpanKey
from ..requests.request_router import RequestRouter, RoutingExceptionBase
from ..requests.request_context import _set_current_span_key, _reset_current_span_key
from ..requests.status import Status
from ..state_keepers.statistics_keeper import StatisticsKeeper

# --------------------------------------------------------------------------------
class ServerBase:
    def __init__(self):
        self._running          : bool             = False
        self._logger           : logging.Logger   = logging.getLogger()
        self._request_router   : RequestRouter    = RequestRouter()
        self._statistics_keeper: StatisticsKeeper = StatisticsKeeper()
        self._transport_type   : str              = ""

    # --------------------------------------------------------------------------------
    def set_transport_type(self, transport_type: str):
        self._transport_type = transport_type

    # --------------------------------------------------------------------------------
    def get_transport_type(self) -> str:
        return self._transport_type

    # --------------------------------------------------------------------------------
    # Used when a frame's header parses but its body fails to msgpack-unpack -- span_key
    # is already known at that point, so a proper ResponseDTO can still be built, instead
    # of just dropping the connection as happens on a header-level read failure.
    def _build_parsing_error_response(self, span_key: SpanKey, error: Exception) -> ResponseDTO:
        return ResponseDTO(
            span_key = span_key,
            status   = Status.PROTOCOL_PARSING_ERROR.value,
            data     = str(error)
        )

    # --------------------------------------------------------------------------------
    # span_key and route_key are already known (sliced off the frame header before the
    # body was even unpacked); data is the already-msgpack-unpacked body. A malformed
    # frame (bad header, bad msgpack) never reaches this point -- see
    # `_build_parsing_error_response`, used by the transport layer for that case instead.
    async def _route_request(self, span_key: SpanKey, route_key: str, data: Any) -> ResponseDTO:
        try:
            start_time   = timeit.default_timer()
            protocol_dto = RequestDTO(span_key=span_key, route_key=route_key, data=data)
            token        = _set_current_span_key(span_key)
            try:
                request      = {
                    "span_key"    : span_key,
                    "protocol_dto": protocol_dto,
                }
                response     = await self._request_router.route_request(**request)
                end_time     = timeit.default_timer() - start_time
                self._statistics_keeper.add_endpoint_stats(protocol_dto.route_key, end_time)
                return ResponseDTO(
                    span_key = span_key,
                    status   = Status.SUCCESS.value,
                    data     = response
                )
            finally:
                _reset_current_span_key(token)
        except ValidationError as e:
            return ResponseDTO(
                span_key = span_key,
                status   = Status.VALIDATION_ERROR.value,
                data     = str(e)
            )
        except RoutingExceptionBase as e:
            return ResponseDTO(
                span_key = span_key,
                status   = e.status,
                data     = e.message
            )
        except Exception as e:
            return ResponseDTO(
                span_key = span_key,
                status   = Status.UNHANDLED.value,
                data     = str(e)
            )
