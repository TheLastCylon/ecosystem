from ekosis.sending.sender import sender
from ekosis.sending.buffered_sender import buffered_sender
from ekosis.data_transfer_objects import BufferedEndpointResponseDTO

from .clients import transient_tcp_client, no_such_tcp_server
from ..dtos.dtos import AppRequestDto, AppResponseDto

# --------------------------------------------------------------------------------
def make_request_dto(message: str) -> AppRequestDto:
    return AppRequestDto(message=message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.b.endpoint", AppResponseDto)
async def app_a_sender_app_b_endpoint(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@sender(transient_tcp_client, "app.b.buffered_endpoint", BufferedEndpointResponseDTO)
async def app_a_sender_app_b_buffered_endpoint(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@buffered_sender(transient_tcp_client, "app.b.buffered_endpoint", AppRequestDto, BufferedEndpointResponseDTO)
async def app_a_buffered_sender_app_b_buffered_endpoint(message: str):
    return make_request_dto(message)

# --------------------------------------------------------------------------------
@buffered_sender(no_such_tcp_server, "no_server_exists", AppRequestDto, BufferedEndpointResponseDTO)
async def app_a_buffered_sender_no_server(message: str, **kwargs):
    return make_request_dto(message)
