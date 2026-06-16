import os
import uuid
import pytest

from ekosis.queues.pending_queue import PendingQueue, PendingEntry
from ekosis.middleware.buffered_middleware_base import BufferedMiddlewareBase
from ekosis.middleware.buffered_middleware_manager import BufferedMiddlewareManager
from ekosis.util.singleton import SingletonType
from ekosis.data_transfer_objects.json_protocol import SpanKey

# --------------------------------------------------------------------------------
_BASENAME      = "test_buffered_middleware"
PENDING_SQLITE = f"/tmp/{_BASENAME}-pending.sqlite"
ERROR_SQLITE   = f"/tmp/{_BASENAME}-error.sqlite"

for _f in [PENDING_SQLITE, ERROR_SQLITE]:
    if os.path.exists(_f):
        os.remove(_f)

QUEUE: PendingQueue = PendingQueue("/tmp", _BASENAME, 10)

# --------------------------------------------------------------------------------
# Helpers

def _make_span_key() -> SpanKey:
    return SpanKey.generate()

def _make_entry(span_key: SpanKey, data: str, metadata: dict = None) -> PendingEntry:
    return PendingEntry(
        span_key = _make_span_key(),
        data     = data,
        retries  = 0,
        metadata = metadata or {},
    )

# --------------------------------------------------------------------------------
# PendingEntry -- metadata survives push/pop in memory

@pytest.mark.asyncio
async def test_pending_metadata_survives_memory_push_pop():
    item_span_key = _make_span_key()
    await QUEUE.push_pending(item_span_key, "data", 0, {"trace_id": 42, "span_id": 7})
    result = await QUEUE.pending_q.pop()
    assert result.metadata == {"trace_id": 42, "span_id": 7}

# --------------------------------------------------------------------------------
# PendingEntry -- metadata survives SQLite page write/load

@pytest.mark.asyncio
async def test_pending_metadata_survives_sqlite_page_boundary():
    target_span_key = _make_span_key()
    # fill past two full pages (page_size=10) to force target into SQLite
    for _ in range(21):
        await QUEUE.push_pending(_make_span_key(), "filler", 0, {})
    await QUEUE.push_pending(target_span_key, "target_data", 0, {"trace_id": 99, "span_id": 3})
    # drain until we reach target
    found = None
    while QUEUE.pending_q.size() > 0:
        entry = await QUEUE.pending_q.pop()
        if entry and entry.span_key == target_span_key:
            found = entry
            break
    await QUEUE.pending_q.clear()
    assert found is not None
    assert found.metadata == {"trace_id": 99, "span_id": 3}

# --------------------------------------------------------------------------------
# ErrorEntry -- metadata survives push_error / pop

@pytest.mark.asyncio
async def test_error_metadata_survives_push_pop():
    item_span_key = _make_span_key()
    await QUEUE.push_error(item_span_key, "data", "test failure", {"trace_id": 11, "span_id": 5})
    result = await QUEUE.error_q.pop()
    assert result.metadata == {"trace_id": 11, "span_id": 5}

# --------------------------------------------------------------------------------
# move_all_error_to_pending -- metadata preserved, not regenerated

@pytest.mark.asyncio
async def test_metadata_survives_move_all_error_to_pending():
    item_span_key = _make_span_key()
    await QUEUE.push_error(item_span_key, "data", "failure", {"trace_id": 20, "span_id": 8})
    await QUEUE.move_all_error_to_pending()
    result = await QUEUE.pending_q.pop()
    assert result.metadata == {"trace_id": 20, "span_id": 8}
    assert result.retries  == 0

# --------------------------------------------------------------------------------
# move_one_error_to_pending -- metadata preserved, not regenerated

@pytest.mark.asyncio
async def test_metadata_survives_move_one_error_to_pending():
    item_span_key = _make_span_key()
    await QUEUE.push_error(item_span_key, "data", "failure", {"trace_id": 30, "span_id": 9})
    await QUEUE.move_one_error_to_pending(item_span_key)
    result = await QUEUE.pending_q.pop()
    assert result.metadata == {"trace_id": 30, "span_id": 9}
    assert result.retries  == 0

# --------------------------------------------------------------------------------
# push_pending with no metadata -- defaults to empty dict

@pytest.mark.asyncio
async def test_push_pending_no_metadata_defaults_empty():
    item_span_key = _make_span_key()
    await QUEUE.push_pending(item_span_key, "data")
    result = await QUEUE.pending_q.pop()
    assert result.metadata == {}

# --------------------------------------------------------------------------------
# push_error with no metadata -- defaults to empty dict

@pytest.mark.asyncio
async def test_push_error_no_metadata_defaults_empty():
    item_span_key = _make_span_key()
    await QUEUE.push_error(item_span_key, "data", "reason")
    result = await QUEUE.error_q.pop()
    assert result.metadata == {}

# --------------------------------------------------------------------------------
# BufferedMiddlewareManager -- collect_push_metadata merges multiple middleware dicts

class _MetaMiddleware(BufferedMiddlewareBase):
    def __init__(self, key: str, value):
        self._key   = key
        self._value = value

    async def before_push(self, span_key: SpanKey, dto, **kwargs) -> dict:
        return {self._key: self._value}

class _TrackingMiddleware(BufferedMiddlewareBase):
    def __init__(self):
        self.before_process_calls = []
        self.after_process_calls  = []

    async def before_process(self, span_key, dto, metadata, retries):
        self.before_process_calls.append((span_key, retries))

    async def after_process(self, span_key, dto, metadata, success):
        self.after_process_calls.append((span_key, success))

# Reset the singleton between tests that use it
def _fresh_manager() -> BufferedMiddlewareManager:
    SingletonType._instances.pop(BufferedMiddlewareManager, None)
    return BufferedMiddlewareManager()

@pytest.mark.asyncio
async def test_collect_push_metadata_merges_dicts():
    manager = _fresh_manager()
    manager.add(_MetaMiddleware("trace_id", 1))
    manager.add(_MetaMiddleware("span_id",  2))
    result = await manager.collect_push_metadata(_make_span_key(), None)
    assert result == {"trace_id": 1, "span_id": 2}

@pytest.mark.asyncio
async def test_collect_push_metadata_empty_when_no_middlewares():
    manager = _fresh_manager()
    result  = await manager.collect_push_metadata(_make_span_key(), None)
    assert result == {}

@pytest.mark.asyncio
async def test_before_process_called_with_correct_args():
    manager  = _fresh_manager()
    tracker  = _TrackingMiddleware()
    manager.add(tracker)
    span_key = _make_span_key()
    metadata = {"trace_id": 5}
    await manager.run_before_process(span_key, None, metadata, retries=2)
    assert tracker.before_process_calls == [(span_key, 2)]

@pytest.mark.asyncio
async def test_after_process_called_with_correct_args():
    manager  = _fresh_manager()
    tracker  = _TrackingMiddleware()
    manager.add(tracker)
    span_key = _make_span_key()
    metadata = {"trace_id": 5}
    await manager.run_after_process(span_key, None, metadata, success=True)
    assert tracker.after_process_calls == [(span_key, True)]

@pytest.mark.asyncio
async def test_before_and_after_process_called_in_order():
    manager  = _fresh_manager()
    order    = []

    class _OrderMiddleware(BufferedMiddlewareBase):
        def __init__(self, name):
            self._name = name
        async def before_process(self, span_key, dto, metadata, retries):
            order.append(f"before:{self._name}")
        async def after_process(self, span_key, dto, metadata, success):
            order.append(f"after:{self._name}")

    manager.add(_OrderMiddleware("A"))
    manager.add(_OrderMiddleware("B"))
    span_key = _make_span_key()
    await manager.run_before_process(span_key, None, {}, 0)
    await manager.run_after_process(span_key, None, {}, True)
    assert order == ["before:A", "before:B", "after:A", "after:B"]

# --------------------------------------------------------------------------------
# Reprocess path -- before_push is NOT called; metadata from ErrorEntry is preserved

@pytest.mark.asyncio
async def test_reprocess_does_not_call_before_push():
    manager      = _fresh_manager()
    push_called  = []

    class _PushTracker(BufferedMiddlewareBase):
        async def before_push(self, span_key, dto, **kwargs) -> dict:
            push_called.append(span_key)
            return {}

    manager.add(_PushTracker())

    item_span_key = _make_span_key()
    # Simulate: item was originally pushed with metadata, then failed to error queue
    await QUEUE.push_error(item_span_key, "data", "failure", {"trace_id": 77, "span_id": 4})
    # Reprocess moves it back to pending -- should NOT call before_push
    await QUEUE.move_one_error_to_pending(item_span_key)
    result = await QUEUE.pending_q.pop()

    assert push_called      == []                        # before_push never fired
    assert result.metadata  == {"trace_id": 77, "span_id": 4}  # original metadata intact
