import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementResponseDto,
)

# --------------------------------------------------------------------------------
app_B_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=9998)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.data", QManagementResponseDto)
async def do_eco_queued_handler_data(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.receiving.pause", QManagementResponseDto)
async def do_eco_queued_handler_receiving_pause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.receiving.unpause", QManagementResponseDto)
async def do_eco_queued_handler_receiving_unpause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.processing.pause", QManagementResponseDto)
async def do_eco_queued_handler_processing_pause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.processing.unpause", QManagementResponseDto)
async def do_eco_queued_handler_processing_unpause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.all.pause", QManagementResponseDto)
async def do_eco_queued_handler_all_pause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.all.unpause", QManagementResponseDto)
async def do_eco_queued_handler_all_unpause(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.get_first_10", QManagementResponseDto)
async def do_eco_queued_handler_errors_get_first_10(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.reprocess.all", QManagementResponseDto)
async def do_eco_queued_handler_errors_reprocess_all(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.clear", QManagementResponseDto)
async def do_eco_queued_handler_errors_clear(route_key: str = "app.test_queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# eco.queued_handler.errors.reprocess.one
# eco.queued_handler.errors.pop_request
# eco.queued_handler.errors.inspect_request

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_data():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_data())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_data_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_data("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_pause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_unpause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_pause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_unpause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_pause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_unpause())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_get_first_10():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_get_first_10_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_all():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_all())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_all_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_all("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_clear():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_clear())
    data     = response.model_dump()
    assert 'queue_data' in data

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_clear_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_clear("asdf"))
    assert response.message.startswith("No queue for route key:")

# eco.queued_handler.errors.reprocess.one
# eco.queued_handler.errors.pop_request
# eco.queued_handler.errors.inspect_request
