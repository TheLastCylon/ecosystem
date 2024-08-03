import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects import (
    LogLevelRequestDto,
    LogLevelResponseDto,
    LogBufferRequestDto,
    LogBufferResponseDto,
)

# --------------------------------------------------------------------------------
app_A_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.log.level", LogLevelResponseDto)
async def do_eco_log_level(level: str):
    return LogLevelRequestDto(level=level)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.log.buffer", LogBufferResponseDto)
async def do_eco_log_buffer(size: int):
    return LogBufferRequestDto(size=size)

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_do_eco_statistics_get():
    response = cast(LogLevelResponseDto, await do_eco_log_level('debug'))
    assert response.level == 'debug'
    response = cast(LogLevelResponseDto, await do_eco_log_level('info'))
    assert response.level == 'info'
    response = cast(LogLevelResponseDto, await do_eco_log_level('warn'))
    assert response.level == 'warn'
    response = cast(LogLevelResponseDto, await do_eco_log_level('error'))
    assert response.level == 'error'
    response = cast(LogLevelResponseDto, await do_eco_log_level('critical'))
    assert response.level == 'critical'

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_do_eco_log_buffer():
    response = cast(LogBufferResponseDto, await do_eco_log_buffer(0))
    assert response.size == 0
