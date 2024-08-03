import asyncio
import uuid
import pytest

from typing import cast
from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender
from ekosis.data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementResponseDto,
    QManagementItemRequestDto,
)
from ekosis.data_transfer_objects.queued_endpoint_response import QueuedEndpointResponseDTO
from .dtos.dtos import AppRequestDto

# --------------------------------------------------------------------------------
app_B_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=9998)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.data", QManagementResponseDto)
async def do_eco_queued_handler_data(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.receiving.pause", QManagementResponseDto)
async def do_eco_queued_handler_receiving_pause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.receiving.unpause", QManagementResponseDto)
async def do_eco_queued_handler_receiving_unpause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.processing.pause", QManagementResponseDto)
async def do_eco_queued_handler_processing_pause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.processing.unpause", QManagementResponseDto)
async def do_eco_queued_handler_processing_unpause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.all.pause", QManagementResponseDto)
async def do_eco_queued_handler_all_pause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.all.unpause", QManagementResponseDto)
async def do_eco_queued_handler_all_unpause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.get_first_10", QManagementResponseDto)
async def do_eco_queued_handler_errors_get_first_10(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.reprocess.all", QManagementResponseDto)
async def do_eco_queued_handler_errors_reprocess_all(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.clear", QManagementResponseDto)
async def do_eco_queued_handler_errors_clear(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "app.b.queued_endpoint_fail", QueuedEndpointResponseDTO)
async def do_app_queued_endpoint_fail(message: str, **kwargs):
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.reprocess.one", QManagementResponseDto)
async def do_eco_queued_handler_errors_reprocess_one(uid: str, route_key: str = "app.b.queued_endpoint_fail"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.inspect_request", QManagementResponseDto)
async def do_eco_queued_handler_errors_inspect_request(uid: str, route_key: str = "app.b.queued_endpoint_fail"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

# --------------------------------------------------------------------------------
@sender(app_B_tcp_client, "eco.queued_handler.errors.pop_request", QManagementResponseDto)
async def do_eco_queued_handler_errors_pop_request(uid: str, route_key: str = "app.b.queued_endpoint_fail"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

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
    assert response.queue_data.receiving_paused is True

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_unpause())
    assert response.queue_data.receiving_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_receiving_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_receiving_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_pause())
    assert response.queue_data.processing_paused is True

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_unpause())
    assert response.queue_data.processing_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_processing_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_processing_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_pause())
    assert response.queue_data.receiving_paused is True
    assert response.queue_data.processing_paused is True

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_pause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_unpause())
    assert response.queue_data.receiving_paused is False
    assert response.queue_data.processing_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_all_unpause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_all_unpause("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_get_first_10():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10())
    assert len(response.queue_data) == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_get_first_10_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_all():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_all())
    assert response.queue_data.database_sizes.error == 0
    assert response.queue_data.receiving_paused is False
    assert response.queue_data.processing_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_all_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_all("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_clear():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_clear())
    assert response.queue_data.database_sizes.error == 0
    assert response.queue_data.receiving_paused is False
    assert response.queue_data.processing_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_clear_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_clear("asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_one_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_one("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_inspect_request_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_inspect_request("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_pop_request_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_pop_request("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_one_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_one(uuid_to_use, "asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_inspect_request_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_inspect_request(uuid_to_use, "asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_pop_request_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_pop_request(uuid_to_use, "asdf"))
    assert response.message.startswith("No queue for route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_one_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_one(uuid_to_use))
    assert response.message.startswith("No request with uid ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_inspect_request_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_inspect_request(uuid_to_use))
    assert response.message.startswith("No request with uid ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_pop_request_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_handler_errors_pop_request(uuid_to_use))
    assert response.message.startswith("No request with uid ")

UUID_TO_USE = uuid.uuid4()
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_one():
    uuid_to_use = UUID_TO_USE
    response_1  = cast(QueuedEndpointResponseDTO, await do_app_queued_endpoint_fail("Test Message", request_uid=uuid_to_use))
    assert str(uuid_to_use) == response_1.uid
    response_2  = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("app.b.queued_endpoint_fail"))
    while len(response_2.queue_data) < 1:
        await asyncio.sleep(1)
        response_2  = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("app.b.queued_endpoint_fail"))
    assert str(uuid_to_use) == response_2.queue_data[0]
    response_3  = cast(QManagementResponseDto, await do_eco_queued_handler_errors_reprocess_one(str(uuid_to_use)))
    assert response_3.queue_data.database_sizes.pending == 1
    assert response_3.queue_data.database_sizes.error == 0
    assert response_3.queue_data.receiving_paused is False
    assert response_3.queue_data.processing_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_inspect_request():
    uuid_to_use   = UUID_TO_USE
    response_1    = cast(QManagementResponseDto, await do_eco_queued_handler_data("app.b.queued_endpoint_fail"))
    while response_1.queue_data.database_sizes.error < 1:
        await asyncio.sleep(1)
        response_1 = cast(QManagementResponseDto, await do_eco_queued_handler_data("app.b.queued_endpoint_fail"))
    assert response_1.queue_data.receiving_paused is False
    assert response_1.queue_data.processing_paused is False
    assert response_1.queue_data.database_sizes.pending == 0
    assert response_1.queue_data.database_sizes.error > 0
    response_2    = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("app.b.queued_endpoint_fail"))
    assert str(uuid_to_use) == response_2.queue_data[0]
    response      = cast(QManagementResponseDto, await do_eco_queued_handler_errors_inspect_request(str(uuid_to_use)))
    check_message = response.model_dump()
    assert check_message["request_data"]["message"] == "Test Message"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_pop_request():
    uuid_to_use   = UUID_TO_USE
    response_1    = cast(QManagementResponseDto, await do_eco_queued_handler_errors_get_first_10("app.b.queued_endpoint_fail"))
    assert str(uuid_to_use) == response_1.queue_data[0]
    response_2    = cast(QManagementResponseDto, await do_eco_queued_handler_errors_pop_request(str(uuid_to_use)))
    assert response_2.queue_data.receiving_paused is False
    assert response_2.queue_data.processing_paused is False
    assert response_2.queue_data.database_sizes.error == 0
    assert response_2.queue_data.database_sizes.pending == 0
    check_message = response_2.model_dump()
    assert check_message["request_data"]["message"] == "Test Message"
