import asyncio

from ekosis.clients import TCPClient, UDPClient, UDSClient
from ekosis.sending.sender import sender

from .dtos import EchoRequestDto, EchoResponseDto

client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
client_uds = UDSClient("/tmp/echo_example_0_uds.sock")


# --------------------------------------------------------------------------------
def make_echo_request_dto(message: str) -> EchoRequestDto:
    return EchoRequestDto(message=message)


# --------------------------------------------------------------------------------
@sender(client_tcp, "echo", EchoResponseDto)
async def tcp_send(message: str):
    return make_echo_request_dto(message)


# --------------------------------------------------------------------------------
@sender(client_udp, "echo", EchoResponseDto)
async def udp_send(message: str):
    return make_echo_request_dto(message)


# --------------------------------------------------------------------------------
@sender(client_uds, "echo", EchoResponseDto)
async def uds_send(message: str):
    return make_echo_request_dto(message)


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
