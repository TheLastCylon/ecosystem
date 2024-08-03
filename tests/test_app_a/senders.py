from ekosis.sending.sender import sender
from ekosis.sending.queued_sender import queued_sender
from ekosis.data_transfer_objects import QueuedEndpointResponseDTO

from .clients import transient_tcp_client
from ..dtos.dtos import AppRequestDto, AppResponseDto

# --------------------------------------------------------------------------------
def make_request_dto(message: str) -> AppRequestDto:
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.b.endpoint", AppResponseDto)
async def app_a_sender_app_b_endpoint(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.b.queued_endpoint", QueuedEndpointResponseDTO)
async def app_a_sender_app_b_queued_endpoint(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@queued_sender(transient_tcp_client, "app.b.queued_endpoint", AppRequestDto, QueuedEndpointResponseDTO)
async def app_a_queued_sender_app_b_queued_endpoint(message: str):
    return make_request_dto(message)
