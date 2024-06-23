import uuid

from typing import Any, Type, TypeVar, Generic, List
from pydantic import BaseModel as PydanticBaseModel

from .sender_base import SenderBase

from ..clients import ClientBase
from ..data_transfer_objects import EmptyDto
from ..queues import SqlPersistedQueue
from ..state_keepers import StatisticsKeeper
from ..exceptions import ServerBusyException, CommunicationsMaxRetriesReached

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class QueuedRequestDTO(PydanticBaseModel):
    uid    : str
    retries: int = 0
    request: Any


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
    running                 : bool                                = False
    processor_send_running  : bool                                = False
    processor_retry_running : bool                                = False
    _sending_paused         : bool                                = True
    _retrying_paused        : bool                                = True
    statistics_keeper       : StatisticsKeeper                    = StatisticsKeeper()
    directory               : str                                 = None
    queue_file_name_base    : str                                 = None
    queue_file_name_in      : str                                 = None
    queue_file_name_error   : str                                 = None
    max_uncommited          : int                                 = None
    max_retries             : int                                 = None
    send_queue_file_path    : str                                 = None
    retry_queue_file_path   : str                                 = None
    error_queue_file_path   : str                                 = None
    send_queue              : SqlPersistedQueue[QueuedRequestDTO] = None
    retry_queue             : SqlPersistedQueue[QueuedRequestDTO] = None
    error_queue             : SqlPersistedQueue[QueuedRequestDTO] = None

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
        self.max_uncommited = max_uncommited
        self.max_retries    = max_retries

    # --------------------------------------------------------------------------------
    async def enqueue(self, request_data: _RequestDTOType, request_uuid: uuid.UUID = uuid.uuid4()) -> None:
        data_to_queue = QueuedRequestDTO(uid=str(request_uuid), retries=0, request=request_data)
        await self.send_queue.push_back(data_to_queue, request_uuid)
        await self.__check_process_send_queue()

    # --------------------------------------------------------------------------------
    async def __check_process_send_queue(self):
        if not self.processor_send_running:
            asyncio.create_task(self.__process_send_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.

    # --------------------------------------------------------------------------------
    async def __check_process_retry_queue(self):
        if not self.processor_retry_running:
            asyncio.create_task(self.__process_retry_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.

    # --------------------------------------------------------------------------------
    # TODO: Some kind of delay between send attempts
    async def __process_send_queue(self) -> None:
        self.processor_send_running = True
        if not self._sending_paused:
            while not await self.send_queue.is_empty():
                queued_request      = await self.send_queue.pop_front()
                queued_request_uid  = uuid.UUID(queued_request.uid)
                queued_request_data = self._request_dto_type(**queued_request.request)

                try:
                    await self.send_data(queued_request_data, queued_request_uid)
                except (ServerBusyException, CommunicationsMaxRetriesReached): # Only retry sending, if the sending is retryable
                    queued_request.retries += 1
                    await self.retry_queue.push_back(queued_request, queued_request_uid)
                    await self.__check_process_retry_queue()
                except Exception: # Move it to the error queue
                    # TODO: Store the reason for the error in the error queue
                    await self.error_queue.push_back(queued_request, queued_request_uid)
        self.processor_send_running = False

    # --------------------------------------------------------------------------------
    # - attempt to send the message
    #    - On success -> Done!
    #    - On fail:
    #        - Still retryable     -> Put message in back of retry queue
    #        - On retries exceeded -> Put message in error queue
    # TODO: Some kind of delay between send attempts
    async def __process_retry_queue(self) -> None:
        self.processor_retry_running = True
        if not self._retrying_paused:
            while not await self.retry_queue.is_empty():
                queued_request      = await self.retry_queue.pop_front()
                queued_request_uid  = uuid.UUID(queued_request.uid)
                queued_request_data = self._request_dto_type(**queued_request.request)

                try:
                    await self.send_data(queued_request_data, queued_request_uid)
                except (ServerBusyException, CommunicationsMaxRetriesReached): # Only retry sending, if the sending is retryable
                    if queued_request.retries >= self.max_retries:
                        await self.error_queue.push_back(queued_request, queued_request_uid)
                    else:
                        queued_request.retries += 1
                        await self.retry_queue.push_back(queued_request, queued_request_uid)
                except Exception: # Move it to the error queue
                    # TODO: Store the reason for the error in the error queue
                    await self.error_queue.push_back(queued_request, queued_request_uid)
        self.processor_retry_running = False

    # --------------------------------------------------------------------------------
    async def send(self, *args, **kwargs):
        pass
