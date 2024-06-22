from typing import Type, TypeVar, Generic
from pydantic import BaseModel as PydanticBaseModel

from ecosystem.clients import TCPClient
from ecosystem.clients import UDPClient
from ecosystem.clients import UDSClient
from ecosystem.data_transfer_objects.empty import EmptyDto

_RequestDTOType  = TypeVar("_RequestDTOType" , bound=PydanticBaseModel)
_ResponseDTOType = TypeVar("_ResponseDTOType", bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class ClientBase(Generic[_RequestDTOType, _ResponseDTOType]):
    _tcp_client       : TCPClient              = TCPClient(server_host='127.0.0.1', server_port=8888)
    _udp_client       : UDPClient              = UDPClient(server_host='127.0.0.1', server_port=8889)
    _uds_client       : UDSClient              = UDSClient("/tmp/dice_roller_example_0_uds.sock")
    _route_key        : str                    = None
    _request_type_dto : Type[_RequestDTOType]  = None
    _response_type_dto: Type[_ResponseDTOType] = None

    def __init__(
        self,
        route_key        : str,
        request_type_dto : Type[_RequestDTOType]  = EmptyDto,
        response_type_dto: Type[_ResponseDTOType] = EmptyDto,
    ):
        self._route_key         = route_key
        self._request_type_dto  = request_type_dto
        self._response_type_dto = response_type_dto

    async def send_tcp(self, data: _RequestDTOType) -> _ResponseDTOType:
        return await self._tcp_client.send_message(
            self._route_key,
            data,
            self._response_type_dto
        )

    async def send_udp(self, data: _RequestDTOType) -> _ResponseDTOType:
        return await self._udp_client.send_message(
            self._route_key,
            data,
            self._response_type_dto
        )

    async def send_uds(self, data: _RequestDTOType) -> _ResponseDTOType:
        return await self._udp_client.send_message(
            self._route_key,
            data,
            self._response_type_dto
        )
