import json
import logging

from pydantic import ValidationError

from ..logs import EcoLogger
from ..data_transfer_objects import RequestDTO, ResponseDTO
from ..exceptions import RoutingExceptionBase
from ..requests import RequestRouter
from ..requests import Status


# --------------------------------------------------------------------------------
class ServerBase:
    _running       : bool          = False
    _logger        : EcoLogger     = EcoLogger()
    _request_router: RequestRouter = RequestRouter()

    def __init__(self):
        pass

    # --------------------------------------------------------------------------------
    async def _route_request(self, request_data: str) -> ResponseDTO:
        request_uuid: str = ""
        try:
            request_dict = json.loads(request_data.strip())
            self._logger.info(f"_route_request: {request_dict}")
            request      = RequestDTO(**request_dict)
            request_uuid = request.uid
            response     = await self._request_router.route_request(request)
            self._logger.info(f"_route_request response: {response}")
            self._logger.info(f"_route_request response json: {response.json()}")
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.SUCCESS.value,
                data   = response
            )
        except json.decoder.JSONDecodeError as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.JSON_PARSING_ERROR.value,
                data   = str(e)
            )
        except ValidationError as e:
            return ResponseDTO(
                uid    = request_uuid,
                status = Status.JSON_PARSING_ERROR.value,
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
