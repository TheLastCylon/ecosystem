import asyncio
from ecosystem.clients import TCPClient, UDPClient, UDSClient

from .clients.guess import GuessEndpointClient
from .clients.roll import RollEndpointClient
from .clients.roll_times import RollTimesEndpointClient


# --------------------------------------------------------------------------------
async def main():
    tcp_client = TCPClient(server_host='127.0.0.1', server_port=8888)
    udp_client = UDPClient(server_host='127.0.0.1', server_port=8889)
    uds_client = UDSClient("/tmp/dice_roller_example_0_uds.sock")

    guess_client      = GuessEndpointClient(tcp_client, udp_client, uds_client)
    roll_client       = RollEndpointClient(tcp_client, udp_client, uds_client)
    roll_times_client = RollTimesEndpointClient(tcp_client, udp_client, uds_client)

    try:
        await guess_client.send_message()
        await roll_client.send_message(20)
        await roll_times_client.send_message(20, 10)
    except Exception as e:
        print(str(e))
        return

asyncio.run(main())
