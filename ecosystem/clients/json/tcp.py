import asyncio
import json
import uuid

from typing import Type
from pydantic import BaseModel as PydanticBaseModel

from ..client_base import ClientBase

from ...data_transfer_objects import RequestDTO, ResponseDTO, EmptyDto

from ...exceptions import TCPCommunicationsFailureRetryable
from ...exceptions import TCPCommunicationsFailureNonRetryable
from ...exceptions import TCPCommunicationsFailureMaxRetriesReached
from ...exceptions import TCPCommunicationsFailureEmptyResponse


# --------------------------------------------------------------------------------
class TCPClient(ClientBase):
    def __init__(self, server_host: str, server_port: int, max_retries: int = 3, timeout: int = 5):
        self.server_host: str   = server_host
        self.server_port: int   = server_port
        self.max_retries: int   = max_retries
        self.timeout    : int   = timeout
        self.success    : bool  = False
        self.retry_count: int   = 0

    # --------------------------------------------------------------------------------
    async def send_message(
        self,
        route_key        : str,
        data             : PydanticBaseModel,
        response_dto_type: Type[PydanticBaseModel] = EmptyDto
    ) -> PydanticBaseModel:
        self.success     = False
        self.retry_count = 0

        request     = RequestDTO(uid=str(uuid.uuid4()), route_key = route_key, data = data)
        request_str = request.json()

        while self.retry_count < self.max_retries and not self.success:
            try:
                response_str  = await asyncio.create_task(self.__send_message(f"{request_str}\n"))
                response_dict = json.loads(response_str)
                response      = ResponseDTO(**response_dict)
                response_dto  = response_dto_type(**response.data)
                self.success  = True
                return response_dto
            except TCPCommunicationsFailureRetryable as e:
                await asyncio.sleep(1)
                self.retry_count += 1

        if not self.success:
            if self.retry_count >= self.max_retries:
                raise TCPCommunicationsFailureMaxRetriesReached(self.server_host, self.server_port)

    # --------------------------------------------------------------------------------
    async def __send_message(self, request: str) -> str:
        try:
            reader, writer = await asyncio.open_connection(
                self.server_host,
                self.server_port,
            )
            writer.write(request.encode())

            data = await reader.readline()
            if not data:
                raise TCPCommunicationsFailureEmptyResponse(self.server_host, self.server_port)

            response_str = data.decode()

            writer.close()
            await writer.wait_closed()
            return response_str
        except asyncio.TimeoutError as e:
            raise TCPCommunicationsFailureRetryable(self.server_host, self.server_port, str(e))
        except ConnectionResetError as e:
            raise TCPCommunicationsFailureRetryable(self.server_host, self.server_port, str(e))
        except BrokenPipeError as e:
            raise TCPCommunicationsFailureRetryable(self.server_host, self.server_port, str(e))
        except ConnectionRefusedError as e:
            raise TCPCommunicationsFailureNonRetryable(self.server_host, self.server_port, str(e))
        except Exception as e:
            raise TCPCommunicationsFailureNonRetryable(self.server_host, self.server_port, str(e))


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
