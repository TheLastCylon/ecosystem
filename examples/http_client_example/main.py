from fastapi import FastAPI

from ekosis.clients import UDPClient
from ekosis.sending.sender import sender

from dtos import EchoRequestDto, EchoResponseDto

test_client = UDPClient("127.0.0.1", 8889)

@sender(test_client, "echo", EchoResponseDto)
async def echo_endpoint(message: str, **kwargs):
    return EchoRequestDto(message=message)

app = FastAPI()

@app.post("/")
async def root(dto: EchoRequestDto):
    return await echo_endpoint(dto.message)
