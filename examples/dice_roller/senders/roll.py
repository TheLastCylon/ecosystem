from ecosystem.sending import SenderBase
from ecosystem.clients import ClientBase

from ..dtos import RollRequestDto, RollResponseDto


# --------------------------------------------------------------------------------
class RollDXSender(SenderBase[RollRequestDto, RollResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "roll", RollRequestDto, RollResponseDto)

    async def send(self, number_of_sides: int):
        request_data = RollRequestDto(sides=number_of_sides)
        return await self.send_data(request_data)
