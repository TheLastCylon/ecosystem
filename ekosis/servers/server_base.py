import uuid
import json
import logging
import timeit

from pydantic import ValidationError

from ..data_transfer_objects import RequestDTO, ResponseDTO
from ..requests.request_router import RequestRouter, RoutingExceptionBase
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

# request
#   dict
#   text
#   protocol_dto
#   endpoint
#   uuid
#   dto
    # --------------------------------------------------------------------------------
    def set_transport_type(self, transport_type: str):
        self._transport_type = transport_type

    # --------------------------------------------------------------------------------
    def get_transport_type(self) -> str:
        return self._transport_type

    # --------------------------------------------------------------------------------
    async def _route_request(self, request_text: str) -> ResponseDTO:
        uid: str = ""
        try:
            start_time   = timeit.default_timer()
            request_dict = json.loads(request_text.strip())
            protocol_dto = RequestDTO(**request_dict)
            uid          = protocol_dto.uid
            request      = {
                "uid"         : uuid.UUID(uid),
                "protocol_dto": protocol_dto,
            }
            response     = await self._request_router.route_request(**request)
            end_time     = timeit.default_timer() - start_time
            self._statistics_keeper.add_endpoint_stats(protocol_dto.route_key, end_time)
            return ResponseDTO(
                uid    = uid,
                status = Status.SUCCESS.value,
                data   = response
            )
        except json.decoder.JSONDecodeError as e:
            return ResponseDTO(
                uid    = uid,
                status = Status.PROTOCOL_PARSING_ERROR.value,
                data   = str(e)
            )
        except ValidationError as e:
            return ResponseDTO(
                uid    = uid,
                status = Status.PYDANTIC_VALIDATION_ERROR.value,
                data   = str(e)
            )
        except RoutingExceptionBase as e:
            return ResponseDTO(
                uid    = uid,
                status = e.status,
                data   = e.message
            )
        except Exception as e:
            return ResponseDTO(
                uid    = uid,
                status = Status.UNHANDLED.value,
                data   = str(e)
            )
