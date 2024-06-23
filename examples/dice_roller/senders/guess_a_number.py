from ecosystem.sending import SenderBase
from ecosystem.clients import ClientBase
from ecosystem.data_transfer_objects import EmptyDto

from ..dtos import GuessANumberResponseDto


# --------------------------------------------------------------------------------
class GuessANumberSender(SenderBase[EmptyDto, GuessANumberResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "guess", EmptyDto, GuessANumberResponseDto)

    async def send(self):
        request_data = EmptyDto()
        return await self.send_data(request_data)
