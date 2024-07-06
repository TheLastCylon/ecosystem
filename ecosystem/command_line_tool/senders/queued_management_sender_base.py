import json

from typing import List

from ...data_transfer_objects.queue_management import (
    QManagementRequestDto,
    QManagementItemRequestDto,
    QManagementResponseDto
)

from ...sending.sender_base import SenderBase
from ...clients import ClientBase


# --------------------------------------------------------------------------------
def print_response(response: QManagementResponseDto):
    print("================================================================================")
    print(f"{response.message}")
    print("--------------------------------------------------------------------------------")
    if isinstance(response.queue_data, List):
        print(f"First 10 error UUIDs:\n{json.dumps(response.queue_data, indent=4)}")
    elif response.queue_data is not None:
        print(f"Queue information:\n{response.queue_data.model_dump_json(indent=4)}")
    if response.request_data:
        print("--------------------------------------------------------------------------------")
        print(f"Request information:\n{json.dumps(response.request_data, indent=4)}")
    print("================================================================================")


# --------------------------------------------------------------------------------
class QueueManagementSenderBase(SenderBase[QManagementRequestDto, QManagementResponseDto]):
    def __init__(self, client: ClientBase, route_key: str):
        super().__init__(
            client,
            route_key,
            QManagementRequestDto,
            QManagementResponseDto
        )

    async def send(self, queue_route_key: str):
        request_data = QManagementRequestDto(queue_route_key=queue_route_key)
        response = await self.send_data(request_data)
        print_response(response)


# --------------------------------------------------------------------------------
class QueueManagementItemSenderBase(SenderBase[QManagementItemRequestDto, QManagementResponseDto]):
    def __init__(self, client: ClientBase, route_key: str):
        super().__init__(
            client,
            route_key,
            QManagementItemRequestDto,
            QManagementResponseDto
        )

    async def send(self, queue_route_key: str, request_uid: str):
        request_data = QManagementItemRequestDto(
            queue_route_key = queue_route_key,
            request_uid     = request_uid
        )
        response = await self.send_data(request_data)
        print_response(response)
