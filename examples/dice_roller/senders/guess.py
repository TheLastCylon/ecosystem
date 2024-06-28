from ecosystem.sending import SenderBase
from ecosystem.clients import ClientBase
from ecosystem.data_transfer_objects import EmptyDto

from ..dtos import GuessResponseDto


# --------------------------------------------------------------------------------
class GuessANumberSender(SenderBase[EmptyDto, GuessResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "guess", EmptyDto, GuessResponseDto)

    async def send(self):
        request_data = EmptyDto()
        return await self.send_data(request_data)
