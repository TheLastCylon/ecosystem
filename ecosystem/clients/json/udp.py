import asyncio
import json
import uuid

from pydantic import BaseModel as PydanticBaseModel

from ..client_base import ClientBase

from ...data_transfer_objects import RequestDTO, ResponseDTO

from ...exceptions import UDPCommunicationsFailureEmptyResponse
from ...exceptions import UDPCommunicationsFailureRetryable
from ...exceptions import UDPCommunicationsFailureMaxRetriesReached
from ...exceptions import UDPCommunicationsFailureNonRetryable


# --------------------------------------------------------------------------------
class UDPClient(asyncio.DatagramProtocol, ClientBase):
    def __init__(self, server_host: str, server_port: int, max_retries: int = 3, timeout: int = 5):
        self.server_host: str                       = server_host
        self.server_port: int                       = server_port
        self.max_retries: int                       = max_retries
        self.timeout    : int                       = timeout
        self.request    : str                       = ""
        self.success    : bool                      = False
        self.retry_count: int                       = 0
        self.loop       : asyncio.AbstractEventLoop = None
        self.transport  : asyncio.DatagramTransport = None
        self.on_done    : asyncio.Future            = None

    # --------------------------------------------------------------------------------
    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport
        self.transport.sendto(self.request.encode())

    # --------------------------------------------------------------------------------
    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        if not data:
            self.on_done.set_exception(UDPCommunicationsFailureEmptyResponse(self.server_host, self.server_port))
        else:
            response = data.decode()
            self.transport.close()
            self.on_done.set_result(response)

    # --------------------------------------------------------------------------------
    def error_received(self, exc):
        print(f'error_received: Exception: {str(exc)}')
        self.on_done.set_exception(exc)

    # --------------------------------------------------------------------------------
    def connection_lost(self, exc):
        if exc:
            print(f'connection_lost: Exception: {str(exc)}')
            self.on_done.set_exception(exc)
        elif not self.on_done.done():
            print('connection_lost: Exception: Connection lost')
            self.on_done.set_exception(Exception('Connection lost')) # TODO: Improve this exception

    # --------------------------------------------------------------------------------
    async def send_message(self,  route_key: str, data: PydanticBaseModel) -> ResponseDTO:
        self.success     = False
        self.retry_count = 0
        request          = RequestDTO(uid=str(uuid.uuid4()), route_key=route_key, data=data)
        request_str      = request.json()
        response_str     = await asyncio.create_task(self.__send_message_retry_loop(f"{request_str}\n"))
        response_dict    = json.loads(response_str)
        response         = ResponseDTO(**response_dict)
        return response

    # --------------------------------------------------------------------------------
    async def __send_message_retry_loop(self, request: str) -> str:
        self.request = request
        while self.retry_count < self.max_retries and not self.success:
            try:
                response     = await self.__send_message()
                self.success = True
                return response
            except UDPCommunicationsFailureRetryable as e:
                self.retry_count += 1

        if not self.success:
            if self.retry_count >= self.max_retries:
                raise UDPCommunicationsFailureMaxRetriesReached(self.server_host, self.server_port)

    # --------------------------------------------------------------------------------
    async def __send_message(self):
        self.loop    = asyncio.get_running_loop()
        self.on_done = self.loop.create_future()

        self.transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: self,
            remote_addr=(self.server_host, self.server_port)
        )

        try:
            return await asyncio.wait_for(self.on_done, timeout=self.timeout)
        except asyncio.TimeoutError as e:
            raise UDPCommunicationsFailureRetryable(self.server_host, self.server_port, str(e))
        except ConnectionRefusedError as e:
            raise UDPCommunicationsFailureNonRetryable(self.server_host, self.server_port, str(e))
        except Exception as e:
            raise UDPCommunicationsFailureNonRetryable(self.server_host, self.server_port, str(e))
        finally:
            self.transport.close()


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
