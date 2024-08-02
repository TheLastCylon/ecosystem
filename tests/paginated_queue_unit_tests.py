import sys
import os
import pytest
import uuid

from typing import Any, List
from pydantic import BaseModel as PydanticBaseModel

from ekosis.queues import PaginatedQueue

# --------------------------------------------------------------------------------
class PendingEntry(PydanticBaseModel):
    uid    : str
    retries: int = 0
    data   : Any

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
async def test_inspect_uuid_where_uuid_does_not_exist():
    result = await PAGINATED_QUEUE.inspect_uuid(uuid.uuid4())
    assert result is None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop_uuid_where_uuid_does_not_exist():
    result = await PAGINATED_QUEUE.pop_uuid(uuid.uuid4())
    assert result is None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_push():
    for i in range(300):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Some data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    assert PAGINATED_QUEUE.size() == 300

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_push_duplicate():
    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Some data",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    assert PAGINATED_QUEUE.size() == 301

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_first_x_uuids():
    result = await PAGINATED_QUEUE.get_first_x_uuids(10)
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
    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Some data",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    assert PAGINATED_QUEUE.size() == 1
    result = await PAGINATED_QUEUE.get_first_x_uuids(10)
    assert len(result) == 1

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_clear():
    for i in range(300):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Some data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_front_page():
    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Inspect UUID data",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_uuid(item_uuid)
    assert pending_entry_data.data == f"Inspect UUID data"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_back_page():
    for i in range(250):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Inspect UUID back_page",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_uuid(item_uuid)
    assert pending_entry_data.data == f"Inspect UUID back_page"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_inspect_uuid_database():
    for i in range(110):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    item_uuid_to_check = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid_to_check),
        data    = f"Inspect checked item UUID",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid_to_check)

    for i in range(90):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.inspect_uuid(item_uuid_to_check)
    assert pending_entry_data.data == f"Inspect checked item UUID"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_front_page():
    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Inspect UUID data",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_uuid(item_uuid)
    assert str(pending_entry_data.data) == f"Inspect UUID data"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_back_page():
    for i in range(250):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    item_uuid = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid),
        data    = f"Inspect UUID back_page",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_uuid(item_uuid)
    assert pending_entry_data.data == f"Inspect UUID back_page"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_pop_uuid_database():
    for i in range(110):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    item_uuid_to_check = uuid.uuid4()
    entry_to_queue = PendingEntry(
        uid     = str(item_uuid_to_check),
        data    = f"Inspect checked item UUID",
        retries = 0,
    )
    await PAGINATED_QUEUE.push(entry_to_queue, item_uuid_to_check)

    for i in range(90):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Inspect UUID data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)

    pending_entry_data: PendingEntry = await PAGINATED_QUEUE.pop_uuid(item_uuid_to_check)
    assert pending_entry_data.data == f"Inspect checked item UUID"
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_loading():
    global PAGINATED_QUEUE
    for i in range(300):
        item_uuid = uuid.uuid4()
        entry_to_queue = PendingEntry(
            uid     = str(item_uuid),
            data    = f"Some data",
            retries = 0,
        )
        await PAGINATED_QUEUE.push(entry_to_queue, item_uuid)
    PAGINATED_QUEUE.shut_down()

    PAGINATED_QUEUE = PaginatedQueue[PendingEntry](SQLITE_FILE, PendingEntry, 10)
    assert PAGINATED_QUEUE.size() == 300
    await PAGINATED_QUEUE.clear()
    assert PAGINATED_QUEUE.size() == 0
