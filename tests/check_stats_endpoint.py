import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects import (
    StatsRequestDto,
    StatsResponseDto,
)

# --------------------------------------------------------------------------------
app_A_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.statistics.get", StatsResponseDto)
async def do_eco_statistics_get(stat_type: str = "gathered"):
    return StatsRequestDto(type=stat_type)

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_statistics_get_current():
    response = cast(StatsResponseDto, await do_eco_statistics_get("current"))
    data     = response.model_dump()
    assert data['statistics']['application']['name'] == "test_app_a"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_statistics_get_gathered():
    response = cast(StatsResponseDto, await do_eco_statistics_get("gathered"))
    data     = response.model_dump()
    assert 'statistics' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_statistics_get_full():
    response = cast(StatsResponseDto, await do_eco_statistics_get("full"))
    data     = response.model_dump()
    assert 'statistics' in data
