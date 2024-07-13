import json

from ...data_transfer_objects import StatsRequestDto, StatsResponseDto
from ...clients.client_base import ClientBase
from ...sending.sender_base import SenderBase


# --------------------------------------------------------------------------------
def print_response(stat_type: str, response: StatsResponseDto):
    print("================================================================================")
    print(f"Retrieved statistics: [{stat_type}]")
    print("--------------------------------------------------------------------------------")
    print(f"{json.dumps(response.statistics, indent=4)}")
    print("================================================================================")


# --------------------------------------------------------------------------------
class EcoStatisticsGetSender(SenderBase[StatsRequestDto, StatsResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(
            client,
            "eco.statistics.get",
            StatsRequestDto,
            StatsResponseDto
        )

    async def send(self, stat_type: str = "current"):
        request_data = StatsRequestDto(type=stat_type)
        response     = await self.send_data(request_data)
        print_response(stat_type, response)
