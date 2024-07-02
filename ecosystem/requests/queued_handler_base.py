import asyncio
import uuid
import logging

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Generic, List


from .handler_base import HandlerBase
from .status import Status

from ..data_transfer_objects import QueuedEndpointResponseDTO
from ..queues import SqlPersistedQueue
from ..state_keepers.statistics_keeper import StatisticsKeeper


_T = TypeVar("_T", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class QueueingExceptionBase(Exception):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")


# --------------------------------------------------------------------------------
class ReceivingPausedException(QueueingExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.APPLICATION_BUSY.value, f"Receiving on '{route_key}' has been paused.")


# --------------------------------------------------------------------------------
class QueuedRequestDTO(PydanticBaseModel):
    uid    : str
    retries: int = 0
    request: Any


# We need to:
#   - receive the request [DONE]
#   - put the request in the incoming queue [DONE]
#   - somehow process the stuff in the queue
# --------------------------------------------------------------------------------
class QueuedRequestHandlerBase(Generic[_T], HandlerBase, ABC):
    running                 : bool                                = False
    _receiving_paused       : bool                                = True
    _processing_paused      : bool                                = True
    statistics_keeper       : StatisticsKeeper                    = StatisticsKeeper()
    log                     : logging.Logger                      = logging.getLogger()
    directory               : str                                 = None
    queue_file_name_base    : str                                 = None
    queue_file_name_in      : str                                 = None
    queue_file_name_error   : str                                 = None
    max_uncommited          : int                                 = None
    max_retries             : int                                 = None
    incoming_queue_file_path: str                                 = None
    error_queue_file_path   : str                                 = None
    incoming_queue          : SqlPersistedQueue[QueuedRequestDTO] = None
    error_queue             : SqlPersistedQueue[QueuedRequestDTO] = None
    on_shutdown_future      : asyncio.Future                      = None
    shutdown                : bool                                = False

    def __init__(
        self,
        route_key       : str,
        request_dto_type: Type[_T],
        max_uncommited  : int = 0,
        max_retries     : int = 0,
    ):
        super().__init__(route_key, request_dto_type)
        self.max_uncommited = max_uncommited
        self.max_retries    = max_retries

    # --------------------------------------------------------------------------------
    def pause_receiving(self):
        self._receiving_paused = True

    def unpause_receiving(self):
        self._receiving_paused = False

    def pause_processing(self):
        self._processing_paused = True

    def unpause_processing(self):
        self._processing_paused = False

    # --------------------------------------------------------------------------------
    async def incoming_queue_size(self) -> int:
        return await self.incoming_queue.size()

    # --------------------------------------------------------------------------------
    async def error_queue_size(self) -> int:
        return await self.error_queue.size()

    # --------------------------------------------------------------------------------
    async def error_queue_clear(self) -> int:
        return await self.error_queue.clear()

    # --------------------------------------------------------------------------------
    async def get_first_x_error_uuids(self, how_many: int = 1) -> List[str]:
        return await self.error_queue.get_first_x_uuids(how_many)

    # --------------------------------------------------------------------------------
    async def pop_request_from_error_queue(self, request_uid: uuid.UUID) -> _T | None:
        queued_request = await self.error_queue.pop_uuid(request_uid)
        if not queued_request:
            return None
        return self.request_dto_type(**queued_request.request)

    # --------------------------------------------------------------------------------
    async def inspect_request_in_error_queue(self, request_uid: uuid.UUID) -> _T | None:
        queued_request = await self.error_queue.inspect_uuid(request_uid)
        if not queued_request:
            return None
        return self.request_dto_type(**queued_request.request)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self):
        self._processing_paused = True
        while not await self.error_queue.is_empty():
            queued_request = await self.error_queue.pop_front()
            await self.incoming_queue.push_back(queued_request, uuid.UUID(queued_request.uid))
        await self.__check_process_queue()
        self._processing_paused = False

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, request_uid: uuid.UUID) -> bool:
        self._processing_paused = True
        queued_request = await self.error_queue.pop_uuid(request_uid)
        if not queued_request:
            return False
        await self.incoming_queue.push_back(queued_request, uuid.UUID(queued_request.uid))
        await self.__check_process_queue()
        self._processing_paused = False
        return True

    # --------------------------------------------------------------------------------
    def __setup_incoming_queue(self):
        self.incoming_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.incoming_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"queued_endpoint_sizes.{self._route_key}.incoming", self.incoming_queue)

    # --------------------------------------------------------------------------------
    def __setup_error_queue(self):
        self.error_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.error_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"queued_endpoint_sizes.{self._route_key}.error", self.error_queue)

    # --------------------------------------------------------------------------------
    def __configure_queue_names(
        self,
        directory       : str,
        application_name: str,
        instance_id     : str,
    ):
        app_instance_string           = f"{application_name}-{instance_id}"
        self.directory                = directory
        self.queue_file_name_base     = f"{app_instance_string}-{self._route_key}-queue"
        self.queue_file_name_in       = f"{self.queue_file_name_base}-incoming"
        self.queue_file_name_error    = f"{self.queue_file_name_base}-error"
        self.incoming_queue_file_path = f"{self.directory}/{self.queue_file_name_in}"
        self.error_queue_file_path    = f"{self.directory}/{self.queue_file_name_error}"

    # --------------------------------------------------------------------------------
    async def setup(
        self,
        directory       : str,
        application_name: str,
        instance_id     : str,
    ):
        route_key = self.get_route_key()
        self.log.info(f"Queued handler [{route_key}] setup.")
        self.__configure_queue_names(directory, application_name, instance_id)
        self.__setup_incoming_queue()
        self.__setup_error_queue()
        self.unpause_receiving()
        self.unpause_processing()

        await self.__check_process_queue()

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
            self.incoming_queue.shut_down()
            self.error_queue.shut_down()
            self.on_shutdown_future.set_result(True)
            self.log.info(f"Queued handler [{route_key}] stopped.")

    # --------------------------------------------------------------------------------
    async def wait_for_shutdown(self):
        while not self.on_shutdown_future.done():
            await asyncio.sleep(1)

    # --------------------------------------------------------------------------------
    async def _process_queue(self):
        self.running = True
        while not self._processing_paused and not await self.incoming_queue.is_empty():
            queued_request      = await self.incoming_queue.pop_front()
            queued_request_uid  = uuid.UUID(queued_request.uid)
            queued_request_data = self.request_dto_type(**queued_request.request)
            if not await self.process_queued_request(queued_request_uid, queued_request_data):
                queued_request.retries += 1
                if queued_request.retries >= self.max_retries:
                    await self.error_queue.push_back(queued_request, queued_request_uid)
                else:
                    await self.incoming_queue.push_back(queued_request, queued_request_uid)
        self.running = False
        self.__shut_down_check()

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def process_queued_request(self, request_uuid: uuid.UUID, request: _T) -> bool:
        pass

    # --------------------------------------------------------------------------------
    async def __check_process_queue(self):
        if not self.running:
            asyncio.create_task(self._process_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.

    # --------------------------------------------------------------------------------
    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        if self._receiving_paused:
            raise ReceivingPausedException(self._route_key)

        data_to_queue = QueuedRequestDTO(uid = str(request_uuid), retries = 0, request = request_data)
        response      = QueuedEndpointResponseDTO(
            uid = str(await self.incoming_queue.push_back(data_to_queue, request_uuid))
        )
        await self.__check_process_queue()
        return response
