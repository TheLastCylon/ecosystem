from .client_base import ClientBase
from .dtos import RollDXTimesRequestDto, RollDXTimesResponseDto


# --------------------------------------------------------------------------------
class RollTimesEndpointClient(ClientBase[RollDXTimesRequestDto, RollDXTimesResponseDto]):
    def __init__(self):
        super().__init__("roll_times", RollDXTimesRequestDto, RollDXTimesResponseDto)

    async def send_message(self, sides: int, how_many: int):
        request_data = RollDXTimesRequestDto(sides=sides, how_many=how_many)
        print(f"RollTimesEndpointClient: TCP Sending sides[{sides}] times[{how_many}]. ", end="")
        tcp_response = await self.send_tcp(request_data)
        print(f"Received: [{tcp_response.uid}]")
        print(f"RollTimesEndpointClient: UDP Sending sides[{sides}] times[{how_many}]. ", end="")
        udp_response = await self.send_udp(request_data)
        print(f"Received: [{udp_response.uid}]")
        print(f"RollTimesEndpointClient: UDS Sending sides[{sides}] times[{how_many}]. ", end="")
        uds_response = await self.send_uds(request_data)
        print(f"Received: [{uds_response.uid}]")
