import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects import (
    ErrorsResponseDto,
    ErrorCleanerRequestDto,
    EmptyDto
)

# --------------------------------------------------------------------------------
app_A_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.error_states.get", ErrorsResponseDto)
async def do_eco_error_states_get():
    return EmptyDto()

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.error_states.clear", ErrorsResponseDto)
async def do_eco_error_states_clear():
    return ErrorCleanerRequestDto(error_id='', count=0)

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_error_states_get():
    response = cast(ErrorsResponseDto, await do_eco_error_states_get())
    assert response.errors is not None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_error_states_clear():
    response = cast(ErrorsResponseDto, await do_eco_error_states_clear())
    assert response.errors is not None
