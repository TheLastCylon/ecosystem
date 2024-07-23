import asyncio
import uuid
import logging

from typing import Type, TypeVar, Generic, List
from pydantic import BaseModel as PydanticBaseModel

from .sender_base import SenderBase

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto
from ..queues.pending_queue import PendingQueue
from ..state_keepers.statistics_keeper import StatisticsKeeper
from ..exceptions import ServerBusyException, CommunicationsMaxRetriesReached

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class QueuedSenderBase(Generic[_RequestDTOType, _ResponseDTOType], SenderBase[_RequestDTOType, _ResponseDTOType]):
    def __init__(
        self,
        client           : ClientBase,
        route_key        : str,
        request_dto_type : Type[_RequestDTOType],
        response_dto_type: Type[_ResponseDTOType] = EmptyDto,
        wait_period      : float                  = 0,
        page_size        : int                    = 100,
        max_retries      : int                    = 0,
    ):
        super().__init__(
            client,
            route_key,
            request_dto_type,
            response_dto_type
        )

        self.running                  : bool             = False
        self._sending_paused          : bool             = True
        self.statistics_keeper        : StatisticsKeeper = StatisticsKeeper()
        self.log                      : logging.Logger   = logging.getLogger()
        self.__send_process_scheduled : bool             = False
        self.wait_period              : float            = wait_period
        self.page_size                : int              = page_size
        self.max_retries              : int              = max_retries
        self.shutdown                 : bool             = False
        self.queue                    : PendingQueue     = None
        self.on_shutdown_future       : asyncio.Future   = None
        self.__send_process_task      : asyncio.Task     = None

    # --------------------------------------------------------------------------------
    async def send(self, *args, **kwargs):
        pass

    # --------------------------------------------------------------------------------
    async def enqueue(self, request_data: _RequestDTOType, request_uuid: uuid.UUID = None) -> None:
        if not request_uuid:
            uuid_to_use = uuid.uuid4()
        else:
            uuid_to_use = request_uuid
        await self.queue.push_pending(uuid_to_use, request_data, 0)
        self.__check_process_send_queue()

    # --------------------------------------------------------------------------------
    def __check_process_send_queue(self):
        if self.__send_process_task is None:
            self.__send_process_task = asyncio.create_task(self.__process_send_queue())
        elif self.__send_process_task.done():
            self.__send_process_task = asyncio.create_task(self.__process_send_queue())

    # --------------------------------------------------------------------------------
    def shut_down(self):
        self.pause_send_process()
        self.shutdown = True
        self.__shut_down_check()

    # --------------------------------------------------------------------------------
    def __shut_down_check(self):
        if not self.running and self.shutdown:
            route_key = self.get_route_key()
            self.log.info(f"Queued sender [{route_key}] stopping.")
            self.queue.shut_down()
            self.on_shutdown_future.set_result(True)
            self.log.info(f"Queued sender [{route_key}] stopped.")

    # --------------------------------------------------------------------------------
    async def wait_for_shutdown(self):
        while not self.on_shutdown_future.done():
            await asyncio.sleep(1)

    # --------------------------------------------------------------------------------
    async def __do_queue_processing(self):
        while not self._sending_paused and self.queue.pending_q.size():
            queued_item  = await self.queue.pop()
            request_uid  = uuid.UUID(queued_item.uid)
            request_data = self._request_dto_type(**queued_item.data)
            retries      = queued_item.retries
            try:
                if self.wait_period > 0:
                    await asyncio.sleep(self.wait_period)
                await self.send_data(request_data, request_uid)
            except (ServerBusyException, CommunicationsMaxRetriesReached): # Only retry sending, if the sending is retryable
                retries += 1
                if retries >= self.max_retries:
                    await self.queue.push_error(request_uid, request_data, "Max retries reached.")
                else:
                    await self.queue.push_pending(request_uid, request_data, retries)
            except Exception as e : # Move it to the error queue
                await self.queue.push_error(request_uid, request_data, str(e))

    # --------------------------------------------------------------------------------
    async def __process_send_queue(self) -> None:
        try:
            self.running = True
            await self.__do_queue_processing()
        finally:
            self.running                  = False
            self.__send_process_scheduled = False
            self.__shut_down_check()

    # --------------------------------------------------------------------------------
    def pause_send_process(self):
        self._sending_paused = True

    def unpause_send_process(self):
        self._sending_paused = False
        self.__check_process_send_queue()

    def is_send_process_paused(self):
        return self._sending_paused

    # --------------------------------------------------------------------------------
    async def pending_queue_size(self) -> int:
        return await self.queue.get_pending_size()

    # --------------------------------------------------------------------------------
    async def error_queue_size(self) -> int:
        return await self.queue.get_error_size()

    # --------------------------------------------------------------------------------
    async def error_queue_clear(self):
        await self.queue.clear_error_queue()

    # --------------------------------------------------------------------------------
    async def get_first_x_error_uuids(self, how_many: int = 1) -> List[str]:
        return await self.queue.get_first_x_error_uuids(how_many)

    # --------------------------------------------------------------------------------
    async def pop_request_from_error_queue(self, request_uid: uuid.UUID):
        queued_request = await self.queue.pop_error_q_uuid(request_uid)
        if not queued_request:
            return None
        return self._request_dto_type(**queued_request)

    # --------------------------------------------------------------------------------
    async def inspect_request_in_error_queue(self, request_uid: uuid.UUID):
        queued_request = await self.queue.inspect_error_q_uuid(request_uid)
        if not queued_request:
            return None
        return self._request_dto_type(**queued_request)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self):
        self._sending_paused = True
        await self.queue.move_all_error_to_pending()
        self.__check_process_send_queue()
        self._sending_paused = False

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, request_uid: uuid.UUID) -> _RequestDTOType | None:
        self._sending_paused = True
        queued_request = await self.queue.move_one_error_to_pending(request_uid)
        self.__check_process_send_queue()
        self._sending_paused = False
        return self._request_dto_type(**queued_request)

    # --------------------------------------------------------------------------------
    def __configure_queue(
        self,
        directory       : str,
        application_name: str,
        instance_id     : str,
    ):
        app_instance_string = f"{application_name}-{instance_id}"
        self.queue = PendingQueue(
            directory,
            f"{app_instance_string}-{self._route_key}-sender",
            self.page_size
        )
        self.statistics_keeper.add_persisted_queue(f"queued_sender_sizes.{self._route_key}.pending", self.queue.pending_q)
        self.statistics_keeper.add_persisted_queue(f"queued_sender_sizes.{self._route_key}.error"  , self.queue.error_q)

    # --------------------------------------------------------------------------------
    async def setup(
        self,
        directory: str,
        application_name: str,
        instance_id     : str,
    ):
        route_key = self.get_route_key()
        self.log.info(f"Queued sender [{route_key}] setup.")
        self.__configure_queue(directory, application_name, instance_id)
        self.unpause_send_process()

        self.__check_process_send_queue()

        loop = asyncio.get_running_loop()
        self.on_shutdown_future = loop.create_future()
        self.log.info(f"Queued sender [{route_key}] setup complete.")
