import uuid

from typing import Dict, List, Any

from ..requests.queued_handler import QueuedHandler
from ..util import SingletonType


# --------------------------------------------------------------------------------
class QueuedHandlerKeeper(metaclass=SingletonType):
    __queued_handlers: Dict[str, QueuedHandler] = {}

    def __init__(self):
        pass

    # --------------------------------------------------------------------------------
    def has_route_key(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        return True

    # --------------------------------------------------------------------------------
    def add_queued_handler(self, queued_handler: QueuedHandler):
        self.__queued_handlers[queued_handler.get_route_key()] = queued_handler

    # --------------------------------------------------------------------------------
    async def get_queue_information(self, route_key: str) -> Dict[str, Any] | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def __get_queue_information(self, route_key: str) -> Dict[str, Any]:
        return {
            "pending"          : await self.__queued_handlers[route_key].pending_queue_size(),
            "error"            : await self.__queued_handlers[route_key].error_queue_size(),
            "receiving_paused" : self.__queued_handlers[route_key].is_receiving_paused(),
            "processing_paused": self.__queued_handlers[route_key].is_processing_paused()
        }

    # --------------------------------------------------------------------------------
    async def get_first_10_error_uuids(self, route_key) -> List[str] | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].get_first_x_error_uuids(10)

    # --------------------------------------------------------------------------------
    async def pause_receiving_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].pause_receiving()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def pause_processing_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].pause_processing()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def pause_all_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].pause_receiving()
        self.__queued_handlers[route_key].pause_processing()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def unpause_receiving_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].unpause_receiving()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def unpause_processing_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].unpause_processing()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def unpause_all_for_queued_handler(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        self.__queued_handlers[route_key].unpause_receiving()
        self.__queued_handlers[route_key].unpause_processing()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def pop_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_handlers.keys():
            return None
        result = await self.__queued_handlers[route_key].pop_request_from_error_queue(request_uid)
        if not result:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = result
        return queue_information

    # --------------------------------------------------------------------------------
    async def inspect_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_handlers.keys():
            return None
        result = await self.__queued_handlers[route_key].inspect_request_in_error_queue(request_uid)
        if not result:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = result.dict()
        return queue_information

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        await self.__queued_handlers[route_key].reprocess_error_queue()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def clear_error_queue(self, route_key: str):
        if route_key not in self.__queued_handlers.keys():
            return None
        await self.__queued_handlers[route_key].error_queue_clear()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_handlers.keys():
            return None
        result = await self.__queued_handlers[route_key].reprocess_error_queue_request_uid(request_uid)
        if not result:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = result.dict()
        return queue_information
