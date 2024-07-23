import asyncio
import uuid
import logging

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, List

from .handler_base import HandlerBase
from .status import Status

from ..util.fire_and_forget_tasks import fire_and_forget_task
from ..data_transfer_objects import QueuedEndpointResponseDTO
from ..queues.pending_queue import PendingQueue
from ..state_keepers.statistics_keeper import StatisticsKeeper

_T = TypeVar("_T", bound=PydanticBaseModel)

# --------------------------------------------------------------------------------
class QueuedRequestHandlerExceptionBase(Exception):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")

# --------------------------------------------------------------------------------
class QueuedRequestHandlerReceivingPausedException(QueuedRequestHandlerExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.APPLICATION_BUSY.value, f"Receiving on '{route_key}' has been paused.")

# --------------------------------------------------------------------------------
class QueuedRequestHandlerBase(Generic[_T], HandlerBase, ABC):
    def __init__(
        self,
        route_key       : str,
        request_dto_type: Type[_T],
        page_size       : int = 0,
        max_retries     : int = 0,
    ):
        super().__init__(route_key, request_dto_type)
        self.running                : bool             = False
        self._receiving_paused      : bool             = True
        self._processing_paused     : bool             = True
        self.__processing_scheduled : bool             = False
        self.statistics_keeper      : StatisticsKeeper = StatisticsKeeper()
        self.log                    : logging.Logger   = logging.getLogger()
        self.page_size              : int              = page_size
        self.max_retries            : int              = max_retries
        self.shutdown               : bool             = False
        self.queue                  : PendingQueue     = None
        self.on_shutdown_future     : asyncio.Future   = None

    # --------------------------------------------------------------------------------
    def pause_receiving(self):
        self._receiving_paused = True

    def unpause_receiving(self):
        self._receiving_paused = False
        self.__check_process_queue()

    def pause_processing(self):
        self._processing_paused = True

    def unpause_processing(self):
        self._processing_paused = False
        self.__check_process_queue()

    def is_receiving_paused(self):
        return self._receiving_paused

    def is_processing_paused(self):
        return self._processing_paused

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
    async def pop_request_from_error_queue(self, request_uid: uuid.UUID) -> _T | None:
        queued_request = await self.queue.pop_error_q_uuid(request_uid)
        if not queued_request:
            return None
        return self.request_dto_type(**queued_request)

    # --------------------------------------------------------------------------------
    async def inspect_request_in_error_queue(self, request_uid: uuid.UUID) -> _T | None:
        queued_request = await self.queue.inspect_error_q_uuid(request_uid)
        if not queued_request:
            return None
        return self.request_dto_type(**queued_request)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self):
        self._processing_paused = True
        await self.queue.move_all_error_to_pending()
        self.__check_process_queue()
        self._processing_paused = False

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, request_uid: uuid.UUID) -> _T | None:
        self._processing_paused = True
        queued_request = await self.queue.move_one_error_to_pending(request_uid)
        self.__check_process_queue()
        self._processing_paused = False
        return self.request_dto_type(**queued_request)

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
            f"{app_instance_string}-{self._route_key}-endpoint",
            self.page_size
        )
        self.statistics_keeper.add_persisted_queue(f"queued_endpoint_sizes.{self._route_key}.pending", self.queue.pending_q)
        self.statistics_keeper.add_persisted_queue(f"queued_endpoint_sizes.{self._route_key}.error"  , self.queue.error_q)

    # --------------------------------------------------------------------------------
    async def setup(
        self,
        directory       : str,
        application_name: str,
        instance_id     : str,
    ):
        route_key = self.get_route_key()
        self.log.info(f"Queued handler [{route_key}] setup.")
        self.__configure_queue(directory, application_name, instance_id)
        self.unpause_receiving()
        self.unpause_processing()

        self.__check_process_queue()

        loop = asyncio.get_running_loop()
        self.on_shutdown_future = loop.create_future()
        self.log.info(f"Queued handler [{route_key}] setup complete.")

    # --------------------------------------------------------------------------------
    def shut_down(self):
        self.pause_receiving()
        self.pause_processing()
        self.shutdown = True
        self.__shut_down_check()

    # --------------------------------------------------------------------------------
    def __shut_down_check(self):
        if not self.running and self.shutdown:
            route_key = self.get_route_key()
            self.log.info(f"Queued handler [{route_key}] stopping.")
            self.queue.shut_down()
            self.on_shutdown_future.set_result(True)
            self.log.info(f"Queued handler [{route_key}] stopped.")

    # --------------------------------------------------------------------------------
    async def wait_for_shutdown(self):
        while not self.on_shutdown_future.done():
            await asyncio.sleep(1)

    # --------------------------------------------------------------------------------
    async def _process_queue(self):
        self.running = True
        while not self._processing_paused and await self.queue.has_pending():
            queued_item  = await self.queue.pop()
            request_uid  = uuid.UUID(queued_item.uid)
            request_data = self.request_dto_type(**queued_item.data)
            retries      = queued_item.retries
            if not await self.process_queued_request(request_uid, request_data):
                retries += 1
                if retries >= self.max_retries:
                    await self.queue.push_error(request_uid, request_data, "Max retries reached.")
                else:
                    await self.queue.push_pending(request_uid, request_data, retries)
        self.running                = False
        self.__processing_scheduled = False
        self.__shut_down_check()

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def process_queued_request(self, request_uuid: uuid.UUID, request: _T) -> bool:
        pass

    # TODO: Investigate if we need process scheduled check here, as for queued sender?
    # --------------------------------------------------------------------------------
    def __check_process_queue(self):
        if not self.running and not self.__processing_scheduled:
            self.__processing_scheduled = True
            fire_and_forget_task(self._process_queue())

    # --------------------------------------------------------------------------------
    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        if self._receiving_paused:
            raise QueuedRequestHandlerReceivingPausedException(self._route_key)
        fire_and_forget_task(self.queue.push_pending(request_uuid, request_data, 0))
        response = QueuedEndpointResponseDTO(uid = str(request_uuid))
        self.__check_process_queue()
        return response
