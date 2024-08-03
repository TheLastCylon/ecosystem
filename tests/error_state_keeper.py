import pytest

from ekosis.state_keepers.error_state_keeper import ErrorStateKeeper
from ekosis.state_keepers.error_state_list import ErrorStateList

ERROR_STATE_KEEPER = ErrorStateKeeper("test_error", "This is a test error.")
ERROR_STATE_LIST   = ErrorStateList()

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_id():
    assert ERROR_STATE_KEEPER.get_id() == "test_error"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_description():
    assert ERROR_STATE_KEEPER.get_description() == "This is a test error."

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_to_dict():
    result = ERROR_STATE_KEEPER.to_dict()
    assert 'error_id' in result.keys()
    assert 'description' in result.keys()
    assert 'count' in result.keys()
    assert result['error_id'] == "test_error"
    assert result['description'] == "This is a test error."
    assert result['count'] == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_to_json():
    result = ERROR_STATE_KEEPER.to_json()
    assert result == '{"error_id": "test_error", "description": "This is a test error.", "count": 0}'

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_str():
    result = str(ERROR_STATE_KEEPER)
    assert result == 'ErrorState: {"error_id": "test_error", "description": "This is a test error.", "count": 0}'

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_increment():
    ERROR_STATE_KEEPER.increment()
    assert ERROR_STATE_KEEPER.get_error_count() == 1
    ERROR_STATE_KEEPER.clear_all()
    assert ERROR_STATE_KEEPER.get_error_count() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_clear_some():
    for i in range(10):
        ERROR_STATE_KEEPER.increment()
    assert ERROR_STATE_KEEPER.get_error_count() == 10
    ERROR_STATE_KEEPER.clear_some(5)
    assert ERROR_STATE_KEEPER.get_error_count() == 5
    ERROR_STATE_KEEPER.clear_some(10)
    assert ERROR_STATE_KEEPER.get_error_count() == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_set():
    assert ERROR_STATE_KEEPER.is_set() is False
    ERROR_STATE_KEEPER.increment()
    assert ERROR_STATE_KEEPER.is_set() is True
    ERROR_STATE_KEEPER.clear_all()
    assert ERROR_STATE_KEEPER.is_set() is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_has_error_id():
    assert ERROR_STATE_LIST.has_error_id("test_error_id") is False
    ERROR_STATE_LIST.increment("test_error_id", "This is a test error.")
    assert ERROR_STATE_LIST.has_error_id("test_error_id") is True

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_clear_some():
    for x in range(10):
        ERROR_STATE_LIST.increment("test_error_id", "This is a test error.")

    assert ERROR_STATE_LIST.error_state_map["TEST_ERROR_ID"].get_error_count() == 11
    ERROR_STATE_LIST.clear_some("test_error_id", 6)
    assert ERROR_STATE_LIST.error_state_map["TEST_ERROR_ID"].get_error_count() == 5

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_get_error_states():
    result = ERROR_STATE_LIST.get_error_states()
    assert len(result) == 1
    assert result[0].get_error_count() == 5
    assert result[0].get_id() == "TEST_ERROR_ID"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_to_json():
    assert str(ERROR_STATE_LIST) == '[{"error_id": "TEST_ERROR_ID", "description": "This is a test error.", "count": 5}]'

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_clear_all():
    assert ERROR_STATE_LIST.error_state_map["TEST_ERROR_ID"].get_error_count() == 5
    ERROR_STATE_LIST.clear_all("test_error_id")
    assert ERROR_STATE_LIST.error_state_map["TEST_ERROR_ID"].get_error_count() == 0
