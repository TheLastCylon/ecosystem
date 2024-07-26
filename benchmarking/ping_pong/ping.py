import sys
import timeit
import asyncio

from typing import List

from ekosis.clients import TCPClient, UDPClient, UDSClient, PersistedTCPClient, PersistedUDSClient
from ekosis.sending.sender import sender

from .dtos import PingRequestDto

client_tcp    = TCPClient(server_host='127.0.0.1', server_port=8888)
client_udp    = UDPClient(server_host='127.0.0.1', server_port=8889)
client_uds    = UDSClient("/tmp/pong_0_uds.sock")
persisted_tcp = PersistedTCPClient(server_host='127.0.0.1', server_port=8888)
persisted_uds = PersistedUDSClient("/tmp/pong_0_uds.sock")

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
@sender(persisted_tcp, "app.ping", PingRequestDto)
async def persisted_tcp_ping():
    return PingRequestDto(message="ping")

# --------------------------------------------------------------------------------
@sender(persisted_uds, "app.ping", PingRequestDto)
async def persisted_uds_ping():
    return PingRequestDto(message="ping")

# --------------------------------------------------------------------------------
def report_run_data(test_type: str, number_of_messages: int, duration_list: List[float]):
    number_of_runs = len(duration_list)
    print(f"{test_type} report:")
    messages_per_second_list = []
    for i in range(number_of_runs):
        messages_per_second = number_of_messages/duration_list[i]
        messages_per_second_list.append(messages_per_second)
        print(f"    run #{i+1}: {number_of_messages}/{duration_list[i]:.6f} = {messages_per_second:.6f} messages/second")
    total_messages = float(sum(messages_per_second_list))
    average_messages_per_second = (total_messages/number_of_runs)
    print(f"Average: {average_messages_per_second:.6f}\n")

# --------------------------------------------------------------------------------
async def do_run(run_name: str, number_of_runs: int, number_of_messages: int, function):
    print(f"Doing {run_name} run:")
    data_keeper = []
    for i in range(number_of_runs):
        start_time = timeit.default_timer()
        for j in range(number_of_messages):
            response = await function()
        end_time   = timeit.default_timer() - start_time
        data_keeper.append(end_time)
    report_run_data(run_name, number_of_messages, data_keeper)

# --------------------------------------------------------------------------------
async def do_timing(number_of_runs: int, number_of_messages: int):
    await do_run("Transient TCP", number_of_runs, number_of_messages, tcp_ping)
    await do_run("Persisted TCP", number_of_runs, number_of_messages, persisted_tcp_ping)
    await do_run("UDP"          , number_of_runs, number_of_messages, udp_ping)
    await do_run("Transient UDS", number_of_runs, number_of_messages, uds_ping)
    await do_run("Persisted UDS", number_of_runs, number_of_messages, persisted_uds_ping)

# --------------------------------------------------------------------------------
async def main():
    if len(sys.argv) < 2:
        number_of_messages = 10000
    else:
        number_of_messages = int(sys.argv[1])

    if len(sys.argv) > 2:
        number_of_runs = int(sys.argv[2])
    else:
        number_of_runs = 1

    await do_timing(number_of_runs, number_of_messages)

# --------------------------------------------------------------------------------
asyncio.run(main())
