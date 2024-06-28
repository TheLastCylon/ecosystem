from ecosystem.sending import sender
from ecosystem.requests import QueuedRequestHandlerResponseDTO

from .tcp_config import tcp_client
from ..dtos import RollTimesRequestDto


@sender(tcp_client, "dice_roller.roll_times", QueuedRequestHandlerResponseDTO)
async def sender_dice_roller_roll_times(sides: int, how_many: int):
    return RollTimesRequestDto(sides=sides, how_many=how_many)


async def roll_several_dice(sides: int, how_many: int):
    print(f"roll_several_dice: sides[{sides}] how_many[{how_many}]. ", end="")
    tcp_response = await sender_dice_roller_roll_times(sides, how_many)
    print(f"Received: [{tcp_response.uid}]")
