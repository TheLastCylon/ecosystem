import asyncio

from ecosystem.clients import TCPClient
from ecosystem.clients import UDPClient
from ecosystem.clients import UDSClient
from ecosystem.data_transfer_objects.empty import EmptyDto
from ecosystem.standard_handlers.statistics import StatisticsRequestDto

from .dtos import RollDXRequestDto
from .dtos import RollDXTimesRequestDto


client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
client_uds = UDSClient("/tmp/dice_roller_0_uds.sock")


# --------------------------------------------------------------------------------
def print_request(client: str, key: str):
    print(f'{client} sending : route_key:[{key}]')


# --------------------------------------------------------------------------------
def print_response(client: str,  response):
    print(f'{client} received: Status:[{response.status}] Data:[{response.data}]')


# --------------------------------------------------------------------------------
async def tcp_send(key, data):
    print_request("TCP", key)
    response = await client_tcp.send_message(key, data)
    print_response("TCP", response)


# --------------------------------------------------------------------------------
async def udp_send(key, data):
    print_request("UDP", key)
    response = await client_udp.send_message(key, data)
    print_response("UDP", response)


# --------------------------------------------------------------------------------
async def uds_send(key, data):
    print_request("UDP", key)
    response = await client_uds.send_message(key, data)
    print_response("UDS", response)


# --------------------------------------------------------------------------------
async def main():
    guess_dto      = EmptyDto()
    roll_dto       = RollDXRequestDto(sides = 20)
    roll_times_dto = RollDXTimesRequestDto(sides = 20, how_many = 10)
    statistics_dto = StatisticsRequestDto(type = "current")

    try:
        # TCP
        await tcp_send("guess"         , guess_dto)
        await tcp_send("roll"          , roll_dto)
        await tcp_send("roll_times"    , roll_times_dto)
        await tcp_send("eco-statistics", statistics_dto)

        # UDP
        await udp_send("guess"         , guess_dto)
        await udp_send("roll"          , roll_dto)
        await udp_send("roll_times"    , roll_times_dto)
        await udp_send("eco-statistics", statistics_dto)

        # UDS
        await uds_send("guess"         , guess_dto)
        await uds_send("roll"          , roll_dto)
        await uds_send("roll_times"    , roll_times_dto)
        await uds_send("eco-statistics", statistics_dto)
    except Exception as e:
        print(str(e))
        return

asyncio.run(main())
