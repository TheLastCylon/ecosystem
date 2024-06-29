import json
import logging

from pydantic import ValidationError

from ..data_transfer_objects import RequestDTO, ResponseDTO
from ..requests.request_router import RequestRouter, RoutingExceptionBase
from ..requests.status import Status


# --------------------------------------------------------------------------------
class ServerBase:
    _running       : bool           = False
    _logger        : logging.Logger = logging.getLogger()
    _request_router: RequestRouter  = RequestRouter()

    def __init__(self):
        pass

    # --------------------------------------------------------------------------------
    async def _route_request(self, request_data: str) -> ResponseDTO:
        request_uuid: str = ""
        try:
            request_dict = json.loads(request_data.strip())
            request      = RequestDTO(**request_dict)
            # self._logger.info(f"_route_request: uid[{request.uid}] route_key[{request.route_key}]")
            request_uuid = request.uid
            response     = await self._request_router.route_request(request)
            # self._logger.info(f"_route_request response json: {response.json()}")
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
