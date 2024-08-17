import pytest

from ekosis.cacheing import LRUCache

lru_cache = LRUCache(10)

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_basic_caching():
    global lru_cache
    assert len(lru_cache) == 0
    lru_cache['0'] = 0
    assert lru_cache['0'] == 0
    assert len(lru_cache) == 1
    assert len(list(lru_cache.keys())) == 1
    assert len(list(lru_cache.values())) == 1

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop_item():
    global lru_cache
    x = lru_cache.pop_item('0')
    assert x == 0
    assert len(lru_cache) == 0
    assert len(list(lru_cache.keys())) == 0
    assert len(list(lru_cache.values())) == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop_item_does_not_exist():
    global lru_cache
    x = lru_cache.pop_item('item_does_not_exist', False)
    assert x is False
    assert len(lru_cache) == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_filling():
    global lru_cache
    lru_cache['0'] = 0
    assert lru_cache['0'] == 0
    assert len(lru_cache) == 1

    lru_cache['1'] = 1
    assert lru_cache['1'] == 1
    assert len(lru_cache) == 2

    lru_cache['2'] = 2
    assert len(lru_cache) == 3
    lru_cache['3'] = 3
    assert len(lru_cache) == 4
    lru_cache['4'] = 4
    assert len(lru_cache) == 5
    lru_cache['5'] = 5
    assert len(lru_cache) == 6
    lru_cache['6'] = 6
    assert len(lru_cache) == 7
    lru_cache['7'] = 7
    assert len(lru_cache) == 8
    lru_cache['8'] = 8
    assert len(lru_cache) == 9
    lru_cache['9'] = 9
    assert len(lru_cache) == 10
    assert len(list(lru_cache.keys())) == 10

    for x in lru_cache.keys():
        assert int(x) == lru_cache[x]

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_overfilling():
    global lru_cache
    lru_cache['10'] = 0
    lru_cache['11'] = 1
    lru_cache['12'] = 2
    lru_cache['13'] = 3
    lru_cache['14'] = 4
    lru_cache['15'] = 5
    lru_cache['16'] = 6
    lru_cache['17'] = 7
    lru_cache['18'] = 8
    lru_cache['19'] = 9

    count = 0
    for x in lru_cache.keys():
        count += 1
        assert int(x) - 10 == lru_cache[x]
    assert count == 10

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_peek():
    global lru_cache
    assert lru_cache.peek('10') == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_peek_does_not_exist():
    global lru_cache
    assert lru_cache.peek('does_not_exist') is None
    assert lru_cache.peek('does_not_exist', False) is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get():
    global lru_cache
    assert lru_cache.get('10') == 0
    assert lru_cache.get('19') == 9

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_does_not_exist():
    global lru_cache
    assert lru_cache.get('does_not_exist') is None
    assert lru_cache.get('does_not_exist', False) is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop():
    global lru_cache
    popped_item = lru_cache.pop()
    assert popped_item[0] == '19'
    assert popped_item[1] == 9
    assert len(lru_cache) == 9

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_keys():
    global lru_cache
    expected_keys = ['10', '11', '12', '13', '14', '15', '16', '17', '18']
    keys = list(lru_cache.keys())
    assert len(keys) == 9
    for i in expected_keys:
        assert i in keys

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_values():
    global lru_cache
    expected_values = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    values = list(lru_cache.values())
    assert len(values) == 9
    for i in expected_values:
        assert i in values

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_items():
    global lru_cache
    for k, v in lru_cache.items():
        assert int(k) - 10 == v

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_iter():
    global lru_cache
    for k in lru_cache:
        assert int(k) - 10 == lru_cache.peek(k)

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_contains():
    global lru_cache
    assert '10' in lru_cache
    assert '0' not in lru_cache

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_del():
    global lru_cache
    del lru_cache['18']
    assert '18' not in lru_cache
    assert len(lru_cache) == 8

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reset_existing():
    global lru_cache
    assert lru_cache.peek('17') == 7
    lru_cache['17'] = 14
    assert lru_cache.peek('17') == 14

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_clear():
    global lru_cache
    assert len(lru_cache) == 8
    lru_cache.clear()
    assert len(lru_cache) == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pop_empty():
    global lru_cache
    assert lru_cache.pop() is None
