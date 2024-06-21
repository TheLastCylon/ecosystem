import uuid

from typing import Dict
from pydantic import BaseModel as PydanticBaseModel

from ..util import SingletonType
from ..requests.request_router import QueuedHandler


class QueuedHandlerKeeper(metaclass=SingletonType):
    __queued_handlers: Dict[str, QueuedHandler] = {}

    def __init__(self):
        pass

    def has_route_key(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        return True

    def add_queued_handler(self, queued_handler: QueuedHandler):
        self.__queued_handlers[queued_handler.get_route_key()] = queued_handler

    def pause_receiving_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].pause_receiving()
        return True

    def pause_processing_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].pause_processing()
        return True

    def unpause_receiving_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].unpause_receiving()
        return True

    def unpause_processing_for_queued_handler(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        self.__queued_handlers[route_key].unpause_processing()
        return True

    async def pop_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID) -> PydanticBaseModel | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].pop_request_from_error_queue(request_uid)

    async def inspect_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].inspect_request_in_error_queue(request_uid)

    async def reprocess_error_queue(self, route_key: str) -> bool:
        if route_key not in self.__queued_handlers.keys():
            return False
        await self.__queued_handlers[route_key].reprocess_error_queue()
        return True

    async def reprocess_error_queue_request_uid(self, route_key: str, request_uid: uuid.UUID) -> bool | None:
        if route_key not in self.__queued_handlers.keys():
            return None
        return await self.__queued_handlers[route_key].reprocess_error_queue_request_uid(request_uid)
