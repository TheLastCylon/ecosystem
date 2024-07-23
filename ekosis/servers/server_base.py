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

    # --------------------------------------------------------------------------------
    async def _route_request(self, request_data: str) -> ResponseDTO:
        request_uuid: str = ""
        try:
            start_time   = timeit.default_timer()
            request_dict = json.loads(request_data.strip())
            request      = RequestDTO(**request_dict)
            request_uuid = request.uid
            response     = await self._request_router.route_request(request)
            end_time     = timeit.default_timer() - start_time
            self._statistics_keeper.add_endpoint_stats(request.route_key, end_time)
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.SUCCESS.value,
                data   = response
            )
        except json.decoder.JSONDecodeError as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.PROTOCOL_PARSING_ERROR.value,
                data   = str(e)
            )
        except ValidationError as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.PYDANTIC_VALIDATION_ERROR.value,
                data   = str(e)
            )
        except RoutingExceptionBase as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = e.status,
                data   = e.message
            )
        except Exception as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.UNKNOWN.value,
                data   = str(e)
            )

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
