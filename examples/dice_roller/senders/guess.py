from ecosystem.sending.sender import sender
from ecosystem.data_transfer_objects import EmptyDto

from .tcp_config import tcp_client
from ..dtos import GuessResponseDto


@sender(tcp_client, "dice_roller.guess", GuessResponseDto)
async def sender_dice_roller_guess():
    return EmptyDto()


async def do_some_guessing():
    print(f"do_some_guessing: Sending. ", end="")
    tcp_response: GuessResponseDto = await sender_dice_roller_guess() # noqa
    print(f"Received: [{tcp_response.number}]")
