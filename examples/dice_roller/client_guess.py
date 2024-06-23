from ecosystem.clients import TCPClient, UDPClient, UDSClient
from .senders import GuessANumberSender


# --------------------------------------------------------------------------------
class GuessEndpointClient:
    def __init__(
        self,
        client_tcp: TCPClient,
        client_udp: UDPClient,
        client_uds: UDSClient,
    ):
        self.tcp_sender = GuessANumberSender(client_tcp)
        self.udp_sender = GuessANumberSender(client_udp)
        self.uds_sender = GuessANumberSender(client_uds)

    async def send_message(self):
        print(f"GuessEndpointClient: TCP Sending. ", end="")
        tcp_response = await self.tcp_sender.send()
        print(f"Received: [{tcp_response.number}]")
        print(f"GuessEndpointClient: UDP Sending. ", end="")
        udp_response = await self.udp_sender.send()
        print(f"Received: [{udp_response.number}]")
        print(f"GuessEndpointClient: UDS Sending. ", end="")
        uds_response = await self.uds_sender.send()
        print(f"Received: [{uds_response.number}]")
