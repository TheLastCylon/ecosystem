import uuid
import logging

from typing import Dict, List, cast
from pydantic import BaseModel as PydanticBaseModel

from .handler_base import HandlerBase
from .queued_handler_base import QueuedRequestHandlerBase
from .status import Status

from ..middleware.manager import MiddlewareManager
from ..data_transfer_objects import RequestDTO
from ..util import SingletonType
from ..state_keepers.statistics_keeper import StatisticsKeeper
from ..exceptions.application_level import ApplicationProcessingException

# --------------------------------------------------------------------------------
class RoutingExceptionBase(Exception):
    def __init__(self, status: int, message: str):
        self.status : int = status
        self.message: str = f"status: [{status}] message: [{message}]"
        super().__init__(self.message)

# --------------------------------------------------------------------------------
class RouterProcessingException(RoutingExceptionBase):
    def __init__(self, route_key: str, message: str):
        super().__init__(Status.PROCESSING_FAILURE.value, f"Processing Failure '{route_key}', message: '{message}'")

# --------------------------------------------------------------------------------
class UnknownRouteKeyException(RoutingExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.ROUTE_KEY_UNKNOWN.value, f"Unknown route key '{route_key}'")

# --------------------------------------------------------------------------------
class RequestRouter(metaclass=SingletonType):
    _logger             : logging.Logger         = logging.getLogger()
    __statistics_keeper : StatisticsKeeper       = StatisticsKeeper()
    __routing_table     : Dict[str, HandlerBase] = {}
    __middleware_manager: MiddlewareManager      = MiddlewareManager()

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

    async def route_request(self, protocol_dto: RequestDTO, **kwargs) -> PydanticBaseModel:
        if protocol_dto.route_key not in self.__routing_table.keys():
            raise UnknownRouteKeyException(protocol_dto.route_key)

        try:
            kwargs["protocol_dto"]  = protocol_dto
            middleware_protocol_dto = await self.__middleware_manager.run_before_routing(**kwargs) # Middleware before routing
            kwargs["protocol_dto"]  = middleware_protocol_dto
            kwargs["response_dto"]  = await self.__routing_table[protocol_dto.route_key].attempt_request(**kwargs)
            kwargs["protocol_dto"]  = middleware_protocol_dto
            response                = await self.__middleware_manager.run_after_routing(**kwargs)  # Middleware after routing
            return response
        except ApplicationProcessingException as e:
            raise RouterProcessingException(protocol_dto.route_key, e.message)
