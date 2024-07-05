import asyncio
import uuid
import logging
import sys
import os

from typing import Any, Type, TypeVar, Generic, List
from pydantic import BaseModel as PydanticBaseModel

from .sender_base import SenderBase

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto
from ..queues import SqlPersistedQueue
from ..state_keepers.statistics_keeper import StatisticsKeeper
from ..exceptions import ServerBusyException, CommunicationsMaxRetriesReached

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class QueuedRequestDTO(PydanticBaseModel):
    uid    : str
    retries: int = 0
    request: Any


# --------------------------------------------------------------------------------
class QueuedRequestErrorDTO(PydanticBaseModel):
    uid    : str
    request: Any
    reason : str


# --------------------------------------------------------------------------------
# Upon sending:
#   - Put it in the send queue
#   - Send processor:
#       - attempt to send the message
#           - On success -> Done!
#           - On fail    -> Put message in retry queue
#   - Retry processor (has a delay of some kind):
#       - attempt to send the message
#           - On success -> Done!
#           - On fail:
#               - On retries exceeded -> Put message in error queue
#               - Still retryable     -> Put message in back of retry queue
# --------------------------------------------------------------------------------
class QueuedSenderBase(
    Generic[_RequestDTOType, _ResponseDTOType],
    SenderBase[_RequestDTOType, _ResponseDTOType]
):
    running                  : bool                                     = False
    processor_send_running   : bool                                     = False
    processor_retry_running  : bool                                     = False
    _send_process_paused     : bool                                     = True
    _retry_process_paused    : bool                                     = True
    statistics_keeper        : StatisticsKeeper                         = StatisticsKeeper()
    __logger                 : logging.Logger                           = logging.getLogger()
    __send_process_scheduled : bool                                     = False
    __retry_process_scheduled: bool                                     = False
    directory                : str                                      = None
    queue_file_name_base     : str                                      = None
    queue_file_name_send     : str                                      = None
    queue_file_name_retry    : str                                      = None
    queue_file_name_error    : str                                      = None
    max_uncommited           : int                                      = None
    max_retries              : int                                      = None
    send_queue_file_path     : str                                      = None
    retry_queue_file_path    : str                                      = None
    error_queue_file_path    : str                                      = None
    send_queue               : SqlPersistedQueue[QueuedRequestDTO]      = None
    retry_queue              : SqlPersistedQueue[QueuedRequestDTO]      = None
    error_queue              : SqlPersistedQueue[QueuedRequestErrorDTO] = None

    def __init__(
        self,
        client           : ClientBase,
        route_key        : str,
        request_dto_type : Type[_RequestDTOType],
        response_dto_type: Type[_ResponseDTOType] = EmptyDto,
        max_uncommited   : int = 0,
        max_retries      : int = 0,
    ):
        super().__init__(
            client,
            route_key,
            request_dto_type,
            response_dto_type
        )
        self.max_uncommited   = max_uncommited
        self.max_retries      = max_retries
        self.application_name = os.path.basename(sys.argv[0]).replace('.py', '')
        self.directory        = "/tmp"
        self.instance         = "0"

        self.__setup_queues()

    # --------------------------------------------------------------------------------
    async def send(self, *args, **kwargs):
        pass

    # Pause
    # --------------------------------------------------------------------------------
    def pause_send_process(self):
        self._send_process_paused = True

    def pause_retry_process(self):
        self._retry_process_paused = True

    def pause_all(self):
        self._send_process_paused  = True
        self._retry_process_paused = True

    # Un-Pause
    # --------------------------------------------------------------------------------
    def unpause_send_process(self):
        self._send_process_paused = False

    def unpause_retry_process(self):
        self._retry_process_paused = False

    def un_pause_all(self):
        self._send_process_paused  = True
        self._retry_process_paused = True

    # Is-Paused
    # --------------------------------------------------------------------------------
    def is_send_process_paused(self):
        return self._send_process_paused

    def is_retry_process_paused(self):
        return self._retry_process_paused

    # Pop
    # --------------------------------------------------------------------------------
    async def pop_request(self, request_uid: uuid.UUID, from_database: str = "error"):
        if from_database == "error":
            queued_request = await self.error_queue.pop_uuid(request_uid)
        elif from_database == "retry":
            queued_request = await self.retry_queue.pop_uuid(request_uid)
        else:
            queued_request = await self.send_queue.pop_uuid(request_uid)
        if not queued_request:
            return None
        return self._request_dto_type(**queued_request.request)

    # Inspect
    # --------------------------------------------------------------------------------
    async def inspect_request(self, request_uid: uuid.UUID, from_database: str = "error"):
        if from_database == "error":
            queued_request = await self.error_queue.inspect_uuid(request_uid)
        elif from_database == "retry":
            queued_request = await self.retry_queue.inspect_uuid(request_uid)
        else:
            queued_request = await self.send_queue.inspect_uuid(request_uid)
        if not queued_request:
            return None
        return self._request_dto_type(**queued_request.request)

    # --------------------------------------------------------------------------------
    async def get_first_x_uuids(self, how_many: int = 1, from_database: str = "error") -> List[str]:
        if from_database == "error":
            return await self.error_queue.get_first_x_uuids(how_many)
        elif from_database == "retry":
            return await self.retry_queue.get_first_x_uuids(how_many)
        else:
            return await self.send_queue.get_first_x_uuids(how_many)

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue(self):
        self._retry_process_paused = True
        while not await self.error_queue.is_empty():
            queued_request = await self.error_queue.pop_front()
            await self.retry_queue.push_back(queued_request, uuid.UUID(queued_request.uid))
        await self.__check_process_retry_queue()
        self._retry_process_paused = False

    # --------------------------------------------------------------------------------
    async def clear_queue_database(self, database: str = 'error') -> int:
        if database == 'error':
            return await self.error_queue.clear()
        elif database == 'retry':
            return await self.retry_queue.clear()
        else:
            return await self.send_queue.clear()

    # --------------------------------------------------------------------------------
    async def reprocess_error_queue_request_uid(self, request_uid: uuid.UUID) -> _RequestDTOType | None:
        self._retry_process_paused = True
        queued_request = await self.error_queue.pop_uuid(request_uid)
        if not queued_request:
            return None
        await self.retry_queue.push_back(queued_request, uuid.UUID(queued_request.uid))
        await self.__check_process_retry_queue()
        self._retry_process_paused = False
        return self._request_dto_type(**queued_request.request)

    # --------------------------------------------------------------------------------
    async def __get_send_queue_size(self):
        return await self.send_queue.size()

    async def __get_retry_queue_size(self):
        return await self.retry_queue.size()

    async def __get_error_queue_size(self):
        return await self.error_queue.size()

    async def get_queue_sizes(self):
        return {
            "send" : await self.send_queue.size(),
            "retry": await self.retry_queue.size(),
            "error": await self.error_queue.size(),
        }

    # --------------------------------------------------------------------------------
    async def enqueue(self, request_data: _RequestDTOType, request_uuid: uuid.UUID = None) -> None:
        if not request_uuid:
            uuid_to_use = uuid.uuid4()
        else:
            uuid_to_use = request_uuid
        self.__logger.info(f"Pushing {request_data} to queue [{self._route_key}] .")
        data_to_queue = QueuedRequestDTO(uid=str(uuid_to_use), retries=0, request=request_data)
        await self.send_queue.push_back(data_to_queue, uuid_to_use)
        await self.__check_process_send_queue()

    # --------------------------------------------------------------------------------
    async def __check_process_send_queue(self):
        if not self.processor_send_running and not self.__send_process_scheduled:
            self.__send_process_scheduled = True
            asyncio.create_task(self.__process_send_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.

    # --------------------------------------------------------------------------------
    async def __check_process_retry_queue(self):
        if not self.processor_retry_running and not self.__retry_process_scheduled:
            self.__retry_process_scheduled = True
            asyncio.create_task(self.__process_retry_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.

    # --------------------------------------------------------------------------------
    async def __push_queued_request_to_error_queue(
        self,
        queued_request: QueuedRequestDTO,
        reason: str
    ):
        self.__logger.info(f"Pushing request to ERROR queue.")
        request_uid = uuid.UUID(queued_request.uid)
        data        = QueuedRequestErrorDTO(
            uid    = queued_request.uid,
            request= queued_request.request,
            reason = reason
        )
        await self.error_queue.push_back(data, request_uid)

    # TODO: Some kind of delay between send attempts
    # --------------------------------------------------------------------------------
    async def __attempt_queued_request_send(
        self,
        queued_request: QueuedRequestDTO,
    ):
        self.__logger.info(f"Attempting send.")
        queued_request_uid  = uuid.UUID(queued_request.uid)
        queued_request_data = self._request_dto_type(**queued_request.request)
        await self.send_data(queued_request_data, queued_request_uid)

    # --------------------------------------------------------------------------------
    async def __push_queued_request_to_retry_queue(
        self,
        queued_request: QueuedRequestDTO,
    ):
        self.__logger.info(f"Pushing request to retry queue.")
        queued_request.retries += 1
        await self.retry_queue.push_back(queued_request, uuid.UUID(queued_request.uid))
        await self.__check_process_retry_queue()

    # --------------------------------------------------------------------------------
    async def __process_send_queue(self) -> None:
        self.processor_send_running = True
        while not self._send_process_paused and not await self.send_queue.is_empty():
            queued_request = await self.send_queue.pop_front()
            try:
                await self.__attempt_queued_request_send(queued_request)
            except (ServerBusyException, CommunicationsMaxRetriesReached) as e: # Only retry sending, if the sending is retryable
                await self.__push_queued_request_to_retry_queue(queued_request)
            except Exception as e : # Move it to the error queue
                await self.__push_queued_request_to_error_queue(queued_request, str(e))
        self.processor_send_running   = False
        self.__send_process_scheduled = False

    # --------------------------------------------------------------------------------
    async def __check_max_retries(
        self,
        queued_request: QueuedRequestDTO,
    ):
        if queued_request.retries >= self.max_retries:
            await self.__push_queued_request_to_error_queue(queued_request, "Max Retries Reached")
        else:
            await self.__push_queued_request_to_retry_queue(queued_request)

    # --------------------------------------------------------------------------------
    async def __process_retry_queue(self) -> None:
        self.processor_retry_running = True
        while not self._retry_process_paused and not await self.retry_queue.is_empty():
            queued_request = await self.retry_queue.pop_front()
            try:
                await self.__attempt_queued_request_send(queued_request)
            except (ServerBusyException, CommunicationsMaxRetriesReached): # Only retry sending, if the sending is retryable
                await self.__check_max_retries(queued_request)
            except Exception as e: # Move it to the error queue
                await self.__push_queued_request_to_error_queue(queued_request, str(e))
        self.processor_retry_running   = False
        self.__retry_process_scheduled = False

    # --------------------------------------------------------------------------------
    def __configure_queue_names(
        self,
        directory       : str,
        application_name: str,
        instance_id     : str,
    ):
        app_instance_string           = f"{application_name}-{instance_id}"
        self.directory                = directory
        self.queue_file_name_base     = f"{app_instance_string}-{self._route_key}-sending-queue-"
        self.queue_file_name_send     = f"{self.queue_file_name_base}send.sqlite"
        self.queue_file_name_retry    = f"{self.queue_file_name_base}retry.sqlite"
        self.queue_file_name_error    = f"{self.queue_file_name_base}error.sqlite"
        self.send_queue_file_path     = f"{self.directory}/{self.queue_file_name_send}"
        self.retry_queue_file_path    = f"{self.directory}/{self.queue_file_name_retry}"
        self.error_queue_file_path    = f"{self.directory}/{self.queue_file_name_error}"

    def __setup_send_queue(self):
        self.send_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.send_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"queued_sender_sizes.{self._route_key}.send", self.send_queue)

    def __setup_retry_queue(self):
        self.retry_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.retry_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"queued_sender_sizes.{self._route_key}.retry", self.retry_queue)

    def __setup_error_queue(self):
        self.error_queue = SqlPersistedQueue[QueuedRequestErrorDTO](
            self.error_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"queued_sender_sizes.{self._route_key}.error", self.error_queue)

    def __setup_queues(self):
        self.__configure_queue_names(self.directory, self.application_name, self.instance)
        self.__setup_send_queue()
        self.__setup_retry_queue()
        self.__setup_error_queue()
        self._send_process_paused  = False
        self._retry_process_paused = False
