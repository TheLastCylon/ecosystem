from ecosystem.sending import SenderBase
from ecosystem.clients import ClientBase

from ..dtos import RollDXRequestDto, RollDXResponseDto


# --------------------------------------------------------------------------------
class RollDXSender(SenderBase[RollDXRequestDto, RollDXResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "roll", RollDXRequestDto, RollDXResponseDto)

    async def send(self, number_of_sides: int):
        request_data = RollDXRequestDto(sides=number_of_sides)
        return await self.send_data(request_data)
