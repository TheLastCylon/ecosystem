import uuid
import pytest

from ekosis.clients import TransientTCPClient
from ekosis.sending.sender import sender

from .dtos.dtos import SetupTasksRanResponseDto

# --------------------------------------------------------------------------------
transient_tcp_client = TransientTCPClient(server_host='127.0.0.1', server_port=9996)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.c.setup_task_ran", SetupTasksRanResponseDto)
async def get_setup_task_ran(**kwargs):
    from ekosis.data_transfer_objects import EmptyDto
    return EmptyDto()

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_setup_tasks_ran():
    response = await get_setup_task_ran(request_uid=uuid.uuid4())
    assert response.ran is True
