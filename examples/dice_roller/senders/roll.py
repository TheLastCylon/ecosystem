from ekosis.sending.sender import sender

from .tcp_config import tcp_client
from ..dtos import RollRequestDto, RollResponseDto


@sender(tcp_client, "dice_roller.roll", RollResponseDto)
async def sender_dice_roller_roll(sides: int):
    return RollRequestDto(sides=sides)


async def roll_a_dice(number_of_sides: int):
    print(f"roll_a_dice: number of sides[{number_of_sides}]. ", end="")
    tcp_response: RollResponseDto = await sender_dice_roller_roll(number_of_sides) # noqa
    print(f"Received: [{tcp_response.result}]")
