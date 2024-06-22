from .client_base import ClientBase
from .dtos import RollDXRequestDto, RollDXResponseDto


# --------------------------------------------------------------------------------
class RollEndpointClient(ClientBase[RollDXRequestDto, RollDXResponseDto]):
    def __init__(self):
        super().__init__("roll", RollDXRequestDto, RollDXResponseDto)

    async def send_message(self, number_of_sides: int):

        request_data = RollDXRequestDto(sides=number_of_sides)
        print(f"RollEndpointClient: TCP Sending number of sides[{number_of_sides}]. ", end="")
        tcp_response = await self.send_tcp(request_data)
        print(f"Received: [{tcp_response.result}]")
        print(f"RollEndpointClient: UDP Sending number of sides[{number_of_sides}]. ", end="")
        udp_response = await self.send_udp(request_data)
        print(f"Received: [{udp_response.result}]")
        print(f"RollEndpointClient: UDS Sending number of sides[{number_of_sides}]. ", end="")
        uds_response = await self.send_uds(request_data)
        print(f"Received: [{uds_response.result}]")
