from typing import Dict

from ..util import SingletonType
from ..requests.queued_handler import QueuedHandler


class QueuedHandlerKeeper(metaclass=SingletonType):
    __queued_handlers: Dict[str, QueuedHandler] = {}

    def __init__(self):
        pass

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
