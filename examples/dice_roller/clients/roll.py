from ecosystem.clients import TCPClient, UDPClient, UDSClient
from ..senders import RollDXSender


# --------------------------------------------------------------------------------
class RollEndpointClient:
    def __init__(
        self,
        client_tcp: TCPClient,
        client_udp: UDPClient,
        client_uds: UDSClient,
    ):
        self.tcp_sender = RollDXSender(client_tcp)
        self.udp_sender = RollDXSender(client_udp)
        self.uds_sender = RollDXSender(client_uds)

    async def send_message(self, number_of_sides: int):
        print(f"RollEndpointClient: TCP Sending number of sides[{number_of_sides}]. ", end="")
        tcp_response = await self.tcp_sender.send(number_of_sides)
        print(f"Received: [{tcp_response.result}]")
        print(f"RollEndpointClient: UDP Sending number of sides[{number_of_sides}]. ", end="")
        udp_response = await self.udp_sender.send(number_of_sides)
        print(f"Received: [{udp_response.result}]")
        print(f"RollEndpointClient: UDS Sending number of sides[{number_of_sides}]. ", end="")
        uds_response = await self.uds_sender.send(number_of_sides)
        print(f"Received: [{uds_response.result}]")
