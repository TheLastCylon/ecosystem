import asyncio
import json
import socket
import uuid

from pydantic import BaseModel as PydanticBaseModel

from ..client_base import ClientBase

from ...data_transfer_objects import RequestDTO, ResponseDTO

from ...exceptions import UDSCommunicationsFailureMaxRetriesReached
from ...exceptions import UDSCommunicationsFailureEmptyResponse
from ...exceptions import UDSCommunicationsFailureRetryable
from ...exceptions import UDSCommunicationsFailureNonRetryable


# --------------------------------------------------------------------------------
class UDSClient(ClientBase):
    def __init__(self, server_path: str, max_retries: int = 3, timeout: int = 5):
        self.server_path : str  = server_path
        self.max_retries : int  = max_retries
        self.timeout     : int  = timeout
        self.success     : bool = False
        self.retry_count : int  = 0
        self.can_transmit: bool = hasattr(socket, "AF_UNIX")

    # --------------------------------------------------------------------------------
    async def send_message(self, route_key: str, data: PydanticBaseModel) -> ResponseDTO:
        if not self.can_transmit:
            raise Exception("UDS communications are not supported on this platform. Will not send message.")

        self.success     = False
        self.retry_count = 0

        request     = RequestDTO(uid=str(uuid.uuid4()), route_key = route_key, data = data)
        request_str = request.json()

        while self.retry_count < self.max_retries and not self.success:
            try:
                response_str  = await asyncio.create_task(self.__send_message(f"{request_str}\n"))
                response_dict = json.loads(response_str)
                response      = ResponseDTO(**response_dict)
                self.success  = True
                return response
            except UDSCommunicationsFailureRetryable as e:
                await asyncio.sleep(1)
                self.retry_count += 1

        if not self.success:
            if self.retry_count >= self.max_retries:
                raise UDSCommunicationsFailureMaxRetriesReached(self.server_path)

    # --------------------------------------------------------------------------------
    async def __send_message(self, request: str) -> str:
        try:
            reader, writer = await asyncio.open_unix_connection(self.server_path)
            writer.write(request.encode())

            data = await reader.readline()
            if not data:
                raise UDSCommunicationsFailureEmptyResponse(self.server_path)

            response_str = data.decode()

            writer.close()
            await writer.wait_closed()
            return response_str
        except asyncio.TimeoutError as e:
            raise UDSCommunicationsFailureRetryable(self.server_path, str(e))
        except ConnectionResetError as e:
            raise UDSCommunicationsFailureRetryable(self.server_path, str(e))
        except BrokenPipeError as e:
            raise UDSCommunicationsFailureRetryable(self.server_path, str(e))
        except ConnectionRefusedError as e:
            raise UDSCommunicationsFailureNonRetryable(self.server_path, str(e))
        except Exception as e:
            raise UDSCommunicationsFailureNonRetryable(self.server_path, str(e))


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
