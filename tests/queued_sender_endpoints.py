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
from .dtos.dtos import AppRequestDto, AppResponseDto

# --------------------------------------------------------------------------------
app_A_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.data", QManagementResponseDto)
async def do_eco_queued_sender_data(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.send_process.pause", QManagementResponseDto)
async def do_eco_queued_sender_send_process_pause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.send_process.unpause", QManagementResponseDto)
async def do_eco_queued_sender_send_process_unpause(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.get_first_10", QManagementResponseDto)
async def do_eco_queued_sender_errors_get_first_10(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.reprocess.all", QManagementResponseDto)
async def do_eco_queued_sender_errors_reprocess_all(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.clear", QManagementResponseDto)
async def do_eco_queued_sender_errors_clear(route_key: str = "app.b.queued_endpoint"):
    return QManagementRequestDto(queue_route_key=route_key)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "app.a.send_no_such_server", AppResponseDto)
async def do_app_send_no_such_server(message: str, **kwargs):
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.reprocess.one", QManagementResponseDto)
async def do_eco_queued_sender_errors_reprocess_one(uid: str, route_key: str = "no_server_exists"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.inspect_request", QManagementResponseDto)
async def do_eco_queued_sender_errors_inspect_request(uid: str, route_key: str = "no_server_exists"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

# --------------------------------------------------------------------------------
@sender(app_A_tcp_client, "eco.queued_sender.errors.pop_request", QManagementResponseDto)
async def do_eco_queued_sender_errors_pop_request(uid: str, route_key: str = "no_server_exists"):
    return QManagementItemRequestDto(queue_route_key=route_key,  request_uid=uid)

# The following tests verify that:
# 1. The expected standard endpoint does exist.
# 2. It returns basic sane data.
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_data():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_data())
    assert response.queue_data.send_process_paused is False
    assert response.queue_data.database_sizes.error == 0
    assert response.queue_data.database_sizes.pending == 0

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_data_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_data("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_pause():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_pause())
    assert response.queue_data.send_process_paused is True

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_pause_invalid_route_key():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_pause("asdf"))
    assert response.message.startswith("No queued sender with route key:")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_send_process_unpause():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_send_process_unpause())
    assert response.queue_data.send_process_paused is False

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

# do_eco_queued_sender_errors_reprocess_one
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_reprocess_one_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_one("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_reprocess_one_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_one(uuid_to_use, "asdf"))
    assert response.message.startswith("No queued sender with route key: ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_reprocess_one_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_one(uuid_to_use))
    assert response.message.startswith("No request with uid ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_inspect_request_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_inspect_request("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_inspect_request_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_inspect_request(uuid_to_use, "asdf"))
    assert response.message.startswith("No queued sender with route key: ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_inspect_request_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_inspect_request(uuid_to_use))
    assert response.message.startswith("No request with uid ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_pop_request_invalid_uid():
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_pop_request("asdf"))
    assert response.message.endswith(" is not a valid UUID.")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_pop_request_invalid_route_key():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_pop_request(uuid_to_use, "asdf"))
    assert response.message.startswith("No queued sender with route key: ")

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_pop_request_valid_uid_not_in_queue():
    uuid_to_use = str(uuid.uuid4())
    response = cast(QManagementResponseDto, await do_eco_queued_sender_errors_pop_request(uuid_to_use))
    assert response.message.startswith("No request with uid ")

UUID_TO_USE = uuid.uuid4()
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_handler_errors_reprocess_one():
    uuid_to_use = UUID_TO_USE
    response_1  = cast(AppResponseDto, await do_app_send_no_such_server("Test Message", request_uid=uuid_to_use))
    assert response_1.message == "Test Message"
    response_2  = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10("no_server_exists"))
    while len(response_2.queue_data) < 1:
        await asyncio.sleep(1)
        response_2  = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10("no_server_exists"))
    assert str(uuid_to_use) == response_2.queue_data[0]
    response_3  = cast(QManagementResponseDto, await do_eco_queued_sender_errors_reprocess_one(str(uuid_to_use)))
    assert response_3.queue_data.database_sizes.pending == 1
    assert response_3.queue_data.database_sizes.error == 0
    assert response_3.queue_data.send_process_paused is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_inspect_request():
    uuid_to_use   = UUID_TO_USE
    response_1    = cast(QManagementResponseDto, await do_eco_queued_sender_data("no_server_exists"))
    while response_1.queue_data.database_sizes.error < 1:
        await asyncio.sleep(1)
        response_1 = cast(QManagementResponseDto, await do_eco_queued_sender_data("no_server_exists"))
    assert response_1.queue_data.send_process_paused is False
    assert response_1.queue_data.database_sizes.pending == 0
    assert response_1.queue_data.database_sizes.error > 0
    response_2    = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10("no_server_exists"))
    assert str(uuid_to_use) == response_2.queue_data[0]
    response      = cast(QManagementResponseDto, await do_eco_queued_sender_errors_inspect_request(str(uuid_to_use)))
    check_message = response.model_dump()
    assert check_message["request_data"]["message"] == "Test Message"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_eco_queued_sender_errors_pop_request():
    uuid_to_use   = UUID_TO_USE
    response_1    = cast(QManagementResponseDto, await do_eco_queued_sender_errors_get_first_10("no_server_exists"))
    assert str(uuid_to_use) == response_1.queue_data[0]
    response_2    = cast(QManagementResponseDto, await do_eco_queued_sender_errors_pop_request(str(uuid_to_use)))
    assert response_2.queue_data.send_process_paused is False
    assert response_2.queue_data.database_sizes.error == 0
    assert response_2.queue_data.database_sizes.pending == 0
    check_message = response_2.model_dump()
    assert check_message["request_data"]["message"] == "Test Message"
