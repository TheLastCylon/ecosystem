from ecosystem.data_transfer_objects.empty import EmptyDto

from .client_base import ClientBase
from .dtos import GuessANumberResponseDto


# --------------------------------------------------------------------------------
class GuessEndpointClient(ClientBase[EmptyDto, GuessANumberResponseDto]):
    def __init__(self):
        super().__init__("guess", EmptyDto, GuessANumberResponseDto)

    async def send_message(self):
        print(f"GuessEndpointClient: TCP Sending. ", end="")
        tcp_response = await self.send_tcp(EmptyDto())
        print(f"Received: [{tcp_response.number}]")
        print(f"GuessEndpointClient: UDP Sending. ", end="")
        udp_response = await self.send_udp(EmptyDto())
        print(f"Received: [{udp_response.number}]")
        print(f"GuessEndpointClient: UDS Sending. ", end="")
        uds_response = await self.send_uds(EmptyDto())
        print(f"Received: [{uds_response.number}]")
