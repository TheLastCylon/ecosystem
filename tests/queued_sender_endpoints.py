import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementResponseDto,
)

# --------------------------------------------------------------------------------
app_A_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.data", QManagementResponseDto)
async def do_eco_queued_sender_data(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.send_process.pause", QManagementResponseDto)
async def do_eco_queued_sender_send_process_pause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.send_process.unpause", QManagementResponseDto)
async def do_eco_queued_sender_send_process_unpause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.get_first_10", QManagementResponseDto)
async def do_eco_queued_sender_errors_get_first_10(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.reprocess.all", QManagementResponseDto)
async def do_eco_queued_sender_errors_reprocess_all(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.clear", QManagementResponseDto)
async def do_eco_queued_sender_errors_clear(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# eco.queued_sender.errors.reprocess.one
# eco.queued_sender.errors.pop_request
# eco.queued_sender.errors.inspect_request

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_data():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_data())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_data_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_data("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_pause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_pause("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_unpause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_unpause("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_get_first_10():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_get_first_10_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_reprocess_all():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_all())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_reprocess_all_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_all("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_clear():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_clear())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_clear_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_clear("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# eco.queued_sender.errors.reprocess.one
# eco.queued_sender.errors.pop_request
# eco.queued_sender.errors.inspect_request
