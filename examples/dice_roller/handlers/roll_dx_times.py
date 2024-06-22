import uuid
import asyncio
import random

from ecosystem import EcoLogger
from ecosystem import queued_endpoint


from ..dtos import RollDXTimesRequestDto


@queued_endpoint("roll_times", RollDXTimesRequestDto)
async def roll_dx_times(request_uuid: uuid.UUID, request: RollDXTimesRequestDto) -> bool:
    log     = EcoLogger()
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
