from ekosis.sending.sender import sender
from ekosis.sending.queued_sender import queued_sender
from ekosis.data_transfer_objects import QueuedEndpointResponseDTO

from .clients import transient_tcp_client
from ..dtos.dtos import AppRequestDto, AppResponseDto

# --------------------------------------------------------------------------------
def make_request_dto(message: str) -> AppRequestDto:
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.test_endpoint", AppResponseDto)
async def test_pass_through_sender(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.test_queued_endpoint", QueuedEndpointResponseDTO)
async def test_queued_endpoint_sender(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@queued_sender(transient_tcp_client, "app.test_queued_endpoint", AppRequestDto, QueuedEndpointResponseDTO)
async def test_queued_sender_sender(message: str):
    return make_request_dto(message)
