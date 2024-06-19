import asyncio
import logging
import uuid

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Generic

from .handler_base import HandlerBase

from ..queues import SqlPersistedQueue

from ..state_keepers import ErrorStateList
from ..state_keepers import StatisticsKeeper

_T = TypeVar("_T", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
# When using a communications queue, to buffer incoming data, the response to the
# immediate request is just an acknowledgement that the message was received and
# validated. No more, no less.
class QueuedRequestHandlerResponseDTO(PydanticBaseModel):
    uid: str


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
    def __init__(
        self,
        route_key       : str,
        description     : str,
        request_dto_type: Type[_T],
        queue_directory : str,
        max_uncommited  : int = 0,
        max_retries     : int = 0,
    ):
        super(QueuedRequestHandlerBase, self).__init__(route_key, description, request_dto_type)
        self.queue_directory         : str                                 = queue_directory
        self.max_uncommited          : int                                 = max_uncommited
        self.max_retries             : int                                 = max_retries
        self.running                 : bool                                = False
        self.queue_file_base_name    : str                                 = None
        self.incoming_queue_file_name: str                                 = None
        self.error_queue_file_name   : str                                 = None
        self.incoming_queue_file_path: str                                 = None
        self.error_queue_file_path   : str                                 = None
        self.incoming_queue          : SqlPersistedQueue[QueuedRequestDTO] = None
        self.error_queue             : SqlPersistedQueue[QueuedRequestDTO] = None

    def configure(
        self,
        logger              : logging.Logger,
        statistics_keeper   : StatisticsKeeper,
        error_state_list    : ErrorStateList,
        application_name    : str,
        application_instance: str
    ):
        self.logger                   = logger
        self.statistics_keeper        = statistics_keeper
        self.error_state_list         = error_state_list
        self.application_name         = application_name
        self.application_instance     = application_instance
        self.queue_file_base_name     = f"{self.application_name}-{self.application_instance}-{self._route_key}-queue-"
        self.incoming_queue_file_name = f"{self.queue_file_base_name}-incoming"
        self.error_queue_file_name    = f"{self.queue_file_base_name}-error"
        self.incoming_queue_file_path = f"{self.queue_directory}/{self.incoming_queue_file_name}"
        self.error_queue_file_path    = f"{self.queue_directory}/{self.error_queue_file_name}"

        self.incoming_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.incoming_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"{self._route_key}-in", self.incoming_queue)

        self.error_queue = SqlPersistedQueue[QueuedRequestDTO](
            self.error_queue_file_path,
            QueuedRequestDTO,
            self.max_uncommited
        )
        self.statistics_keeper.add_persisted_queue(f"{self._route_key}-error", self.error_queue)

    # --------------------------------------------------------------------------------
    async def _process_queue(self):
        self.running = True
        while not await self.incoming_queue.is_empty():
            queued_request      = await self.incoming_queue.pop_front()
            queued_request_uid  = uuid.UUID(queued_request.uid)
            queued_request_data = self.request_dto_type(**queued_request.request)
            if not await self.process_queued_request(queued_request_data):
                queued_request.retries += 1
                if queued_request.retries >= self.max_retries:
                    await self.error_queue.push_back(queued_request, queued_request_uid)
                else:
                    await self.incoming_queue.push_back(queued_request, queued_request_uid)
        self.running = False

    # --------------------------------------------------------------------------------
    @abstractmethod
    async def process_queued_request(self, request: _T) -> bool:
        pass

    # --------------------------------------------------------------------------------
    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        data_to_queue = QueuedRequestDTO(uid = str(request_uuid), retries = 0, request = request_data)
        response      = QueuedRequestHandlerResponseDTO(
            uid = str(await self.incoming_queue.push_back(data_to_queue, request_uuid))
        )

        if not self.running:
            asyncio.create_task(self._process_queue()) # noqa PyCharm warns me that this is not awaited, but it should not be.
        return response
