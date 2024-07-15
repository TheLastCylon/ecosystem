import uuid

from typing import Dict, List, Any

from ..sending.queued_sender_class import QueuedSenderClass
from ..util import SingletonType


# --------------------------------------------------------------------------------
class QueuedSenderKeeper(metaclass=SingletonType):
    __queued_senders: Dict[str, QueuedSenderClass] = {}

    def __init__(self):
        pass

    # --------------------------------------------------------------------------------
    def get_queued_senders(self) -> List[QueuedSenderClass]:
        return [x for x in self.__queued_senders.values()]

    # --------------------------------------------------------------------------------
    def has_route_key(self, route_key: str) -> bool:
        if route_key not in self.__queued_senders.keys():
            return False
        return True

    # --------------------------------------------------------------------------------
    def add_queued_sender(self, queued_sender: QueuedSenderClass):
        self.__queued_senders[queued_sender.get_route_key()] = queued_sender

    # --------------------------------------------------------------------------------
    async def get_queue_information(self, route_key: str) -> Dict[str, Any] | None:
        if route_key not in self.__queued_senders.keys():
            return None
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def __get_queue_information(self, route_key: str) -> Dict[str, Any]:
        return {
            "pending"             : await self.__queued_senders[route_key].pending_queue_size(),
            "error"               : await self.__queued_senders[route_key].error_queue_size(),
            "send_process_paused" : self.__queued_senders[route_key].is_send_process_paused(),
        }

    # --------------------------------------------------------------------------------
    async def pause_send_process(self, route_key: str):
        if route_key not in self.__queued_senders.keys():
            return None
        self.__queued_senders[route_key].pause_send_process()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def un_pause_send_process(self, route_key: str):
        if route_key not in self.__queued_senders.keys():
            return None
        self.__queued_senders[route_key].unpause_send_process()
        return await self.__get_queue_information(route_key)

    # Request popping
    # --------------------------------------------------------------------------------
    async def pop_request_from_error_queue(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_senders.keys():
            return None
        request = await self.__queued_senders[route_key].pop_request_from_error_queue(request_uid)
        if request is None:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = request
        return queue_information

    # Request inspection
    # --------------------------------------------------------------------------------
    async def inspect_request_in_error_queue(self, route_key: str, request_uid: uuid.UUID,):
        if route_key not in self.__queued_senders.keys():
            return None
        request = await self.__queued_senders[route_key].inspect_request_in_error_queue(request_uid)
        if request is None:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = request
        return queue_information

    # --------------------------------------------------------------------------------
    async def get_first_x_error_uuids(self, route_key) -> List[str] | None:
        if route_key not in self.__queued_senders.keys():
            return None
        return await self.__queued_senders[route_key].get_first_x_error_uuids(10)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self, route_key: str):
        if route_key not in self.__queued_senders.keys():
            return None
        await self.__queued_senders[route_key].reprocess_error_queue()
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def clear_error_queue(self, route_key: str):
        if route_key not in self.__queued_senders.keys():
            return None
        await self.__queued_senders[route_key].clear_queue_database('error')
        return await self.__get_queue_information(route_key)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, route_key: str, request_uid: uuid.UUID):
        if route_key not in self.__queued_senders.keys():
            return None
        result = await self.__queued_senders[route_key].reprocess_error_queue_request_uid(request_uid)
        if not result:
            return False
        queue_information = await self.__get_queue_information(route_key)
        queue_information["request_data"] = result.dict()
        return queue_information
