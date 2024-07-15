import uuid
import asyncio
import random
import logging

from ekosis.requests.queued_endpoint import queued_endpoint

from ..dtos import RollTimesRequestDto


@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
async def dice_roller_roll_times(request_uuid: uuid.UUID, request: RollTimesRequestDto) -> bool:
    log     = logging.getLogger()
    numbers = list(range(1, request.sides))

    log.info(f"roll_times[{request_uuid}]: Processing.")
    total_result   = 0
    expected_total = (request.sides * request.how_many)*0.6
    for times in range(request.how_many):
        total_result += random.choice(numbers) + 1

    log.info(f"roll_times[{request_uuid}]: expected_total[{expected_total}] total_result[{total_result}]")
    if total_result < expected_total:
        log.info(f"roll_times[{request_uuid}]: FAIL!")
        await asyncio.sleep(1)
        return False

    log.info(f"roll_times[{request_uuid}]: Success.")
    await asyncio.sleep(1)
    return True
