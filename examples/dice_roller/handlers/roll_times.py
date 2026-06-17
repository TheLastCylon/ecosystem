import asyncio
import random
import logging

from ekosis.requests.buffered_endpoint import buffered_endpoint
from ekosis.data_transfer_objects import SpanKey

from ..dtos import RollTimesRequestDto


@buffered_endpoint("dice_roller.roll_times", RollTimesRequestDto)
async def dice_roller_roll_times(span_key: SpanKey, dto: RollTimesRequestDto) -> bool:
    log     = logging.getLogger()
    numbers = list(range(1, dto.sides))

    log.info(f"roll_times[{span_key}]: Processing.")
    total_result   = 0
    expected_total = (dto.sides*dto.how_many)*0.6
    for times in range(dto.how_many):
        total_result += random.choice(numbers) + 1

    log.info(f"roll_times[{span_key}]: expected_total[{expected_total}] total_result[{total_result}]")
    if total_result < expected_total:
        log.info(f"roll_times[{span_key}]: FAIL!")
        await asyncio.sleep(1)
        return False

    log.info(f"roll_times[{span_key}]: Success.")
    await asyncio.sleep(1)
    return True
