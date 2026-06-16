import os
import pytest
import uuid

from ekosis.queues             import PaginatedQueue
from ekosis.queues.pending_queue import PendingEntry
from ekosis.data_transfer_objects.json_protocol import SpanKey

# --------------------------------------------------------------------------------
SQLITE_FILE = "/tmp/test_queues.sqlite"

if os.path.exists(SQLITE_FILE):
    os.remove(SQLITE_FILE)

# --------------------------------------------------------------------------------
PAGINATED_QUEUE: PaginatedQueue[PendingEntry] = PaginatedQueue[PendingEntry](SQLITE_FILE, PendingEntry, 10)

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_empty_pop():
    result = await PAGINATED_QUEUE.pop()
    assert result is None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_inspect_span_key_where_span_key_does_not_exist():
    result = await PAGINATED_QUEUE.inspect_span_key(SpanKey.generate())
    assert result is None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop_span_key_where_span_key_does_not_exist():
    result = await PAGINATED_QUEUE.pop_span_key(SpanKey.generate())
    assert result is None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_push():
    for i in range(300):
        span_key = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Some data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    assert PAGINATED_QUEUE.size() == 300

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_push_duplicate():
    span_key       = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Some data",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    assert PAGINATED_QUEUE.size() == 301

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_first_x_uuids():
    result = await PAGINATED_QUEUE.get_first_x_span_keys(10)
    assert len(result) == 10

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop():
    for i in range(301):
        await PAGINATED_QUEUE.pop()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_first_x_uuids_with_less_than_amount():
    span_key = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Some data",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    assert PAGINATED_QUEUE.size() == 1
    result = await PAGINATED_QUEUE.get_first_x_span_keys(10)
    assert len(result) == 1

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_clear():
    for i in range(300):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Some data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_front_page():
    span_key       = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Inspect SpanKey data",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_span_key(span_key)
    assert pending_entry_data.data == f"Inspect SpanKey data"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_back_page():
    for i in range(250):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    span_key       = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Inspect SpanKey back_page",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_span_key(span_key)
    assert pending_entry_data.data == f"Inspect SpanKey back_page"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_database():
    for i in range(110):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    item_span_key_to_check = SpanKey.generate()
    entry_to_queue         = PendingEntry(
        span_key = item_span_key_to_check,
        data     = f"Inspect checked item SpanKey",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_span_key_to_check)

    for i in range(90):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_span_key(item_span_key_to_check)
    assert pending_entry_data.data == f"Inspect checked item SpanKey"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_front_page():
    span_key       = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Inspect SpanKey data",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_span_key(span_key)
    assert str(pending_entry_data.data) == f"Inspect SpanKey data"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_back_page():
    for i in range(250):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    span_key       = SpanKey.generate()
    entry_to_queue = PendingEntry(
        span_key = span_key,
        data     = f"Inspect SpanKey back_page",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_span_key(span_key)
    assert pending_entry_data.data == f"Inspect SpanKey back_page"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_database():
    for i in range(110):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    item_span_key_to_check = SpanKey.generate()
    entry_to_queue         = PendingEntry(
        span_key = item_span_key_to_check,
        data     = f"Inspect checked item SpanKey",
        retries  = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_span_key_to_check)

    for i in range(90):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Inspect SpanKey data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_span_key(item_span_key_to_check)
    assert pending_entry_data.data == f"Inspect checked item SpanKey"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_loading():
    global PAGINATED_QUEUE
    for i in range(300):
        span_key       = SpanKey.generate()
        entry_to_queue = PendingEntry(
            span_key = span_key,
            data     = f"Some data",
            retries  = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, span_key)
    PAGINATED_QUEUE.shut_down()

    PAGINATED_QUEUE = PaginatedQueue[PendingEntry](SQLITE_FILE, PendingEntry, 10)
    assert PAGINATED_QUEUE.size() == 300
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0
