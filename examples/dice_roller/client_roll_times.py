from ecosystem.clients import TCPClient, UDPClient, UDSClient
from .senders import RollDXTimesSender


# --------------------------------------------------------------------------------
class RollTimesEndpointClient:
    def __init__(
        self,
        client_tcp: TCPClient,
        client_udp: UDPClient,
        client_uds: UDSClient,
    ):
        self.tcp_sender = RollDXTimesSender(client_tcp)
        self.udp_sender = RollDXTimesSender(client_udp)
        self.uds_sender = RollDXTimesSender(client_uds)

    async def send_message(self, sides: int, how_many: int):
        print(f"RollTimesEndpointClient: TCP Sending sides[{sides}] times[{how_many}]. ", end="")
        tcp_response = await self.tcp_sender.send(sides, how_many)
        print(f"Received: [{tcp_response.uid}]")
        print(f"RollTimesEndpointClient: UDP Sending sides[{sides}] times[{how_many}]. ", end="")
        udp_response = await self.udp_sender.send(sides, how_many)
        print(f"Received: [{udp_response.uid}]")
        print(f"RollTimesEndpointClient: UDS Sending sides[{sides}] times[{how_many}]. ", end="")
        uds_response = await self.uds_sender.send(sides, how_many)
        print(f"Received: [{uds_response.uid}]")
