import uuid

from typing import Dict, Any, List
from pydantic import BaseModel as PydanticBaseModel

from ..util import SingletonType


# --------------------------------------------------------------------------------
class QueuedHandlerKeeper(metaclass=SingletonType):
    # __queued_handlers is supposed to be of type Dict[str, QueuedHandler], but
    # importing it causes circular imports errors. Duck typing to the resque ...
    # I guess.
    __queued_handlers: Dict[str, Any] = {}

    def __init__(self):
        pass

    # --------------------------------------------------------------------------------
    def has_route_key(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        return True

    # --------------------------------------------------------------------------------
    def add_queued_handler(self, queued_handler: Any):
        self.__queued_handlers[queued_handler.get_route_key()] = queued_handler

    # --------------------------------------------------------------------------------
    async def get_queue_sizes(self, route_key: str) -> Dict[str, int] | False:
        if route_key not in self.__queued_handlers.keys():
            return False

        return {
            "incoming": await self.__queued_handlers[route_key].incoming_queue_size(),
            "error"   : await self.__queued_handlers[route_key].error_queue_size(),
        }

    # --------------------------------------------------------------------------------
    async def get_first_10_error_uuids(self, route_key) -> List[str] | False:
        if route_key not in self.__queued_handlers.keys():
            return False

        return await self.__queued_handlers[route_key].get_first_x_error_uuids(10)

    # --------------------------------------------------------------------------------
    def pause_receiving_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].pause_receiving()
        return True

    # --------------------------------------------------------------------------------
    def pause_processing_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].pause_processing()
        return True

    # --------------------------------------------------------------------------------
    def unpause_receiving_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].unpause_receiving()
        return True

    # --------------------------------------------------------------------------------
    def unpause_processing_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].unpause_processing()
        return True

    # --------------------------------------------------------------------------------
    async def pop_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID) -> PydanticBaseModel | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].pop_request_from_error_queue(request_uid)

    # --------------------------------------------------------------------------------
    async def inspect_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].inspect_request_in_error_queue(request_uid)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        await self.__queued_handlers[route_key].reprocess_error_queue()
        return True

    # --------------------------------------------------------------------------------
    async def clear_error_queue(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        await self.__queued_handlers[route_key].error_queue_clear()
        return True

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, route_key: str, request_uid: uuid.UUID) -> bool | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].reprocess_error_queue_request_uid(request_uid)
