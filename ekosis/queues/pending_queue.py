import logging

from typing import Any, List
from pydantic import BaseModel as PydanticBaseModel
from .paginated_queue import PaginatedQueue
from ..data_transfer_objects import SpanKey

log = logging.getLogger()

# --------------------------------------------------------------------------------
class PendingEntry(PydanticBaseModel):
    span_key: SpanKey
    retries : int  = 0
    data    : Any
    metadata: dict = {}

# --------------------------------------------------------------------------------
class ErrorEntry(PydanticBaseModel):
    span_key: SpanKey
    data    : Any
    reason  : str
    metadata: dict = {}

# --------------------------------------------------------------------------------
class PendingQueue:
    pending_q: PaginatedQueue[PendingEntry] = None
    error_q  : PaginatedQueue[ErrorEntry]   = None

    def __init__(
        self,
        directory     : str,
        file_basename : str,
        page_size     : int = 100
    ) -> None:
        self.__setup_pending_q(f"{directory}/{file_basename}-pending.sqlite", page_size)
        self.__setup_error_q  (f"{directory}/{file_basename}-error.sqlite"  , page_size)

    # --------------------------------------------------------------------------------
    def shut_down(self):
        self.pending_q.shut_down()
        self.error_q.shut_down()

    # --------------------------------------------------------------------------------
    async def has_pending(self):
        return not self.pending_q.is_empty()

    async def get_pending_size(self):
        return self.pending_q.size()

    async def get_error_size(self):
        return self.error_q.size()

    async def get_sizes(self):
        return {
            "pending": await self.get_pending_size(),
            "error"  : await self.get_error_size()
        }

    # --------------------------------------------------------------------------------
    async def move_all_error_to_pending(self):
        while self.error_q.size() > 0:
            popped_error_entry = await self.error_q.pop()
            await self.push_pending(popped_error_entry.span_key, popped_error_entry.data, 0, popped_error_entry.metadata)

    async def move_one_error_to_pending(self, span_key: SpanKey):
        popped_error_entry = await self.error_q.pop_span_key(span_key)
        if popped_error_entry:
            await self.push_pending(span_key, popped_error_entry.data, 0, popped_error_entry.metadata)
            return popped_error_entry.data
        return None

    async def clear_error_queue(self):
        await self.error_q.clear()

    async def get_first_x_error_span_keys(self, how_many: int = 1) -> List[str]:
        return await self.error_q.get_first_x_span_keys(how_many)

    # --------------------------------------------------------------------------------
    @staticmethod
    async def _pop_using_span_key(queue: PaginatedQueue, span_key: SpanKey):
        queued_request = await queue.pop_span_key(span_key)
        if not queued_request:
            return None
        return queued_request.data

    async def pop_error_q_span_key(self, span_key: SpanKey) -> Any|None:
        return await self._pop_using_span_key(self.error_q, span_key)

    async def pop_pending_q_span_key(self, span_key: SpanKey) -> Any|None:
        return await self._pop_using_span_key(self.pending_q, span_key)

    # --------------------------------------------------------------------------------
    @staticmethod
    async def _inspect_using_span_key(queue: PaginatedQueue, span_key: SpanKey):
        queued_request = await queue.inspect_span_key(span_key)
        if not queued_request:
            return None
        return queued_request.data

    async def inspect_error_q_span_key(self, span_key: SpanKey) -> Any|None:
        return await self._inspect_using_span_key(self.error_q, span_key)

    async def inspect_pending_q_span_key(self, span_key: SpanKey) -> Any|None:
        return await self._inspect_using_span_key(self.pending_q, span_key)

    # --------------------------------------------------------------------------------
    async def push_pending(self, span_key: SpanKey, item_data, retries: int = 0, metadata: dict | None = None):
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = item_data,
            retries  = retries,
            metadata = metadata or {},
        )
        await self.pending_q.push(entry_to_queue, span_key)

    # --------------------------------------------------------------------------------
    async def push_error(self, span_key: SpanKey, item_data, reason: str, metadata: dict | None = None):
        log.warning(f"Pushing message to error queue [{span_key}] {reason}]")
        entry_to_queue = ErrorEntry(
            span_key = span_key,
            data     = item_data,
            reason   = reason,
            metadata = metadata or {},
        )
        await self.error_q.push(entry_to_queue, span_key)

    # --------------------------------------------------------------------------------
    async def pop(self):
        return await self.pending_q.pop()

    # --------------------------------------------------------------------------------
    def __setup_pending_q(self, file_path: str, page_size: int):
        self.pending_q = PaginatedQueue[PendingEntry](file_path, PendingEntry, page_size)

    # --------------------------------------------------------------------------------
    def __setup_error_q(self, file_path: str, page_size: int):
        self.error_q = PaginatedQueue[ErrorEntry](file_path, ErrorEntry, page_size)
