import uuid
import logging

from typing import Any, List
from pydantic import BaseModel as PydanticBaseModel
from .sql_persisted_queue import SqlPersistedQueue


# --------------------------------------------------------------------------------
class PendingEntry(PydanticBaseModel):
    uid    : str
    retries: int = 0
    data   : Any


# --------------------------------------------------------------------------------
class ErrorEntry(PydanticBaseModel):
    uid   : str
    data  : Any
    reason: str


# --------------------------------------------------------------------------------
class PendingQueue:
    pending_q: SqlPersistedQueue[PendingEntry] = None
    error_q  : SqlPersistedQueue[ErrorEntry]   = None

    def __init__(
        self,
        directory     : str,
        file_basename : str,
        max_uncommited: int = 0
    ) -> None:
        self.__setup_pending_q(f"{directory}/{file_basename}-pending.sqlite", max_uncommited)
        self.__setup_error_q  (f"{directory}/{file_basename}-error.sqlite"  , max_uncommited)

    # --------------------------------------------------------------------------------
    def shut_down(self):
        self.pending_q.shut_down()
        self.error_q.shut_down()

    # --------------------------------------------------------------------------------
    async def has_pending(self):
        return not await self.pending_q.is_empty()

    async def get_pending_size(self):
        return await self.pending_q.size()

    async def get_error_size(self):
        return await self.error_q.size()

    async def get_sizes(self):
        return {
            "pending": await self.get_pending_size(),
            "error"  : await self.get_error_size()
        }

    # --------------------------------------------------------------------------------
    async def move_all_error_to_pending(self):
        while await self.error_q.size() > 0:
            popped_error_entry = await self.error_q.pop_front()
            await self.push_pending(popped_error_entry.uid, popped_error_entry.data, 0)

    async def move_one_error_to_pending(self, item_uid: uuid.UUID):
        popped_error_entry = await self.pop_error_q_uuid(item_uid)
        if popped_error_entry:
            await self.push_pending(popped_error_entry.uid, popped_error_entry.data, 0)
            return popped_error_entry.data
        return None

    async def clear_error_queue(self):
        await self.error_q.clear()

    async def get_first_x_error_uuids(self, how_many: int = 1) -> List[str]:
        return await self.error_q.get_first_x_uuids(how_many)

    # --------------------------------------------------------------------------------
    @staticmethod
    async def _pop_using_uuid(queue: SqlPersistedQueue, item_uid: uuid.UUID):
        queued_request = await queue.pop_uuid(item_uid)
        if not queued_request:
            return None
        return queued_request.data

    async def pop_error_q_uuid(self, request_uid: uuid.UUID) -> Any | None:
        return await self._pop_using_uuid(self.error_q, request_uid)

    async def pop_pending_q_uuid(self, request_uid: uuid.UUID) -> Any | None:
        return await self._pop_using_uuid(self.pending_q, request_uid)

    # --------------------------------------------------------------------------------
    @staticmethod
    async def _inspect_using_uuid(queue: SqlPersistedQueue, item_uid: uuid.UUID):
        queued_request = await queue.inspect_uuid(item_uid)
        if not queued_request:
            return None
        return queued_request.data

    async def inspect_error_q_uuid(self, request_uid: uuid.UUID) -> Any | None:
        return await self._inspect_using_uuid(self.error_q, request_uid)

    async def inspect_pending_q_uuid(self, request_uid: uuid.UUID) -> Any | None:
        return await self._inspect_using_uuid(self.pending_q, request_uid)

    # --------------------------------------------------------------------------------
    async def push_pending(self, item_uuid: uuid.UUID, item_data, retries: int = 0):
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = item_data,
            retries = retries,
        )
        await self.pending_q.push_back(entry_to_queue)

    # --------------------------------------------------------------------------------
    async def push_error(self, item_uuid: uuid.UUID, item_data, reason: str):
        entry_to_queue = ErrorEntry(
            uid    = str(item_uuid),
            data   = item_data,
            reason = reason,
        )
        await self.error_q.push_back(entry_to_queue)

    # --------------------------------------------------------------------------------
    async def pop(self):
        return await self.pending_q.pop_front()

    # --------------------------------------------------------------------------------
    def __setup_pending_q(self, file_path: str, max_uncommited: int = 0):
        self.pending_q = SqlPersistedQueue[PendingEntry](file_path, PendingEntry, max_uncommited)

    # --------------------------------------------------------------------------------
    def __setup_error_q(self, file_path: str, max_uncommited: int = 0):
        self.error_q = SqlPersistedQueue[ErrorEntry](file_path, ErrorEntry, max_uncommited)
