import asyncio

from typing import cast

from ecosystem.clients import TCPClient, UDPClient, UDSClient

from .dtos import EchoRequestDto, EchoResponseDto

client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
client_uds = UDSClient("/tmp/echo_example_0_uds.sock")


# --------------------------------------------------------------------------------
async def tcp_send(message):
    response = await client_tcp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
    return cast(EchoResponseDto, response)


# --------------------------------------------------------------------------------
async def udp_send(message):
    response = await client_udp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
    return cast(EchoResponseDto, response)


# --------------------------------------------------------------------------------
async def uds_send(message):
    response = await client_udp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
    return cast(EchoResponseDto, response)


# --------------------------------------------------------------------------------
async def send_message(message):
    print("========================================")
    print(f"Sending message on TCP: [{message}]")
    response = await tcp_send(message)
    print(f"TCP Response          : [{response.message}]")
    print("----------------------------------------")
    print(f"Sending message on UDP: [{message}]")
    response = await udp_send(message)
    print(f"UDP Response          : [{response.message}]")
    print("----------------------------------------")
    print(f"Sending message on UDS: [{message}]")
    response = await uds_send(message)
    print(f"UDS Response          : [{response.message}]")
    print("========================================")


# --------------------------------------------------------------------------------
async def main():
    try:
        message: str = input('Enter message: ')
        while message != "quit":
            await send_message(message)
            message = input('Enter message: ')
        print("Bye!")
    except Exception as e:
        print(str(e))
        return

# --------------------------------------------------------------------------------
asyncio.run(main())
