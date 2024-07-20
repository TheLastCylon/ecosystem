import uuid

from typing import Dict, List, cast
from pydantic import BaseModel as PydanticBaseModel

from .handler_base import HandlerBase
from .queued_handler_base import QueuedRequestHandlerBase
from .status import Status

from ..data_transfer_objects import RequestDTO
from ..util import SingletonType
from ..state_keepers.statistics_keeper import StatisticsKeeper

# --------------------------------------------------------------------------------
class RoutingExceptionBase(Exception):
    def __init__(self, status: int, message: str):
        self.status : int = status
        self.message: str = f"status: [{status}] message: [{message}]"
        super().__init__(self.message)

# --------------------------------------------------------------------------------
class UnknownRouteKeyException(RoutingExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.ROUTE_KEY_UNKNOWN.value, f"Unknown route key '{route_key}'")

# --------------------------------------------------------------------------------
class RequestRouter(metaclass=SingletonType):
    __statistics_keeper: StatisticsKeeper       = StatisticsKeeper()
    __routing_table    : Dict[str, HandlerBase] = {}

    def register_handler(self, handler: HandlerBase):
        if handler.get_route_key() not in self.__routing_table:
            self.__routing_table[handler.get_route_key()] = handler
            self.__statistics_keeper.track_endpoint_data(handler.get_route_key())
        else:
            raise Exception(f"Handler command id [{handler.get_route_key()}] already exists")

    def get_queued_handlers(self):
        response: List[QueuedRequestHandlerBase] = []
        for queue in self.__routing_table.values():
            if isinstance(queue, QueuedRequestHandlerBase):
                response.append(cast(QueuedRequestHandlerBase, queue))
        return response

    async def route_request(self, request: RequestDTO) -> PydanticBaseModel:
        if request.route_key not in self.__routing_table.keys():
            raise UnknownRouteKeyException(request.route_key)

        return await self.__routing_table[request.route_key].attempt_request(uuid.UUID(request.uid), request.data)

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
