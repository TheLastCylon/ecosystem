from ecosystem.sending import SenderBase
from ecosystem.clients import ClientBase
from ecosystem.requests import QueuedRequestHandlerResponseDTO

from ..dtos import RollDXTimesRequestDto


# --------------------------------------------------------------------------------
class RollDXTimesSender(SenderBase[RollDXTimesRequestDto, QueuedRequestHandlerResponseDTO]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "roll_times", RollDXTimesRequestDto, QueuedRequestHandlerResponseDTO)

    async def send(self, sides: int, how_many: int):
        request_data = RollDXTimesRequestDto(sides=sides, how_many=how_many)
        return await self.send_data(request_data)
