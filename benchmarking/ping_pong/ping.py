import sys
import timeit
import asyncio

from typing import List

from ekosis.clients import TCPClient, UDPClient, UDSClient
from ekosis.sending.sender import sender

from .dtos import PingRequestDto

client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
client_uds = UDSClient("/tmp/pong_0_uds.sock")

data_keeper_tcp = []
data_keeper_udp = []
data_keeper_uds = []

# --------------------------------------------------------------------------------
@sender(client_tcp, "app.ping", PingRequestDto)
async def tcp_ping():
    return PingRequestDto(message="ping")

# --------------------------------------------------------------------------------
@sender(client_udp, "app.ping", PingRequestDto)
async def udp_ping():
    return PingRequestDto(message="ping")

# --------------------------------------------------------------------------------
@sender(client_uds, "app.ping", PingRequestDto)
async def uds_ping():
    return PingRequestDto(message="ping")

# --------------------------------------------------------------------------------
def tcp_benchmark():
    asyncio.run(tcp_ping())

# --------------------------------------------------------------------------------
def udp_benchmark():
    asyncio.run(udp_ping())

# --------------------------------------------------------------------------------
def uds_benchmark():
    asyncio.run(uds_ping())

# --------------------------------------------------------------------------------
def print_timing(test_type: str, how_many: int, duration: float):
    print(f"{test_type}: Sent [{how_many}] in [{duration:.4f}] seconds. i.e. {(how_many/duration):.4f} per second")

# --------------------------------------------------------------------------------
def report_run_data(test_type: str, number_of_messages: int, duration_list: List[float]):
    number_of_runs = len(duration_list)
    print(f"{test_type} report:")
    messages_per_second_list = []
    for i in range(number_of_runs):
        messages_per_second = number_of_messages/duration_list[i]
        messages_per_second_list.append(messages_per_second)
        print(f"    run #{i+1}: {number_of_messages}/{duration_list[i]:.6f} = {messages_per_second:.6f} messages/second")
    print(f"Average: {(sum(messages_per_second_list)/number_of_runs):.6f}\n")

# --------------------------------------------------------------------------------
def do_tcp_timing(how_many: int):
    return timeit.timeit(tcp_benchmark, number=how_many)

# --------------------------------------------------------------------------------
def do_udp_timing(how_many: int):
    return timeit.timeit(udp_benchmark, number=how_many)

# --------------------------------------------------------------------------------
def do_uds_timing(how_many: int):
    return timeit.timeit(uds_benchmark, number=how_many)

# --------------------------------------------------------------------------------
def do_timing(number_of_runs: int, number_of_messages: int):
    print("Doing TCP run:")
    for i in range(number_of_runs):
        data_keeper_tcp.append(do_tcp_timing(number_of_messages))
    report_run_data("TCP", number_of_messages, data_keeper_tcp)

    print("Doing UDP run:")
    for i in range(number_of_runs):
        data_keeper_udp.append(do_udp_timing(number_of_messages))
    report_run_data("UDP", number_of_messages, data_keeper_udp)

    print("Doing UDS run:")
    for i in range(number_of_runs):
        data_keeper_uds.append(do_uds_timing(number_of_messages))
    report_run_data("UDS", number_of_messages, data_keeper_uds)

# --------------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        number_of_messages = 10000
    else:
        number_of_messages = int(sys.argv[1])

    if len(sys.argv) > 2:
        number_of_runs = int(sys.argv[2])
    else:
        number_of_runs = 1

    do_timing(number_of_runs, number_of_messages)

# --------------------------------------------------------------------------------
main()
