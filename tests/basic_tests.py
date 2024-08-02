import pytest

from ekosis.clients import (
    TransientTCPClient,
    PersistedTCPClient,
    TransientUDSClient,
    PersistedUDSClient,
    UDPClient,
)
from ekosis.sending.sender import sender
from .test_app.dtos import AppRequestDto, AppResponseDto

# --------------------------------------------------------------------------------
transient_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=8888)
persisted_tcp_client = PersistedTCPClient(server_host='127.0.0.1', server_port=8888)
transient_uds_client = TransientUDSClient("/tmp/test_app_0_uds.sock")
persisted_uds_client = PersistedUDSClient("/tmp/test_app_0_uds.sock")
udp_client           = UDPClient(server_host='127.0.0.1', server_port=8889)

# --------------------------------------------------------------------------------
def make_request_dto(message: str) -> AppRequestDto:
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.test_endpoint", AppResponseDto)
async def transient_tcp_send(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(persisted_tcp_client, "app.test_endpoint", AppResponseDto)
async def persisted_tcp_send(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(transient_uds_client, "app.test_endpoint", AppResponseDto)
async def transient_uds_send(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(persisted_uds_client, "app.test_endpoint", AppResponseDto)
async def persisted_uds_send(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(udp_client, "app.test_endpoint", AppResponseDto)
async def udp_send(message: str):
    return make_request_dto(message)

# Tests
# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transient_tcp_echo():
    response = await transient_tcp_send(message="test echo")
    assert response.message == "test echo"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_persisted_tcp_echo():
    response = await persisted_tcp_send(message="test echo")
    assert response.message == "test echo"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transient_uds_echo():
    response = await transient_uds_send(message="test echo")
    assert response.message == "test echo"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_persisted_uds_echo():
    response = await persisted_uds_send(message="test echo")
    assert response.message == "test echo"

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_udp_echo():
    response = await udp_send(message="test echo")
    assert response.message == "test echo"
