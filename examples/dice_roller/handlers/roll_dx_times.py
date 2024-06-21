import asyncio
import random

from ecosystem import EcoLogger
from ecosystem import queued_endpoint


from ..dtos import RollDXTimesRequestDto


@queued_endpoint("roll_times", RollDXTimesRequestDto)
async def roll_dx_times(request: RollDXTimesRequestDto) -> bool:
    log     = EcoLogger()
    numbers = list(range(1, request.sides))

    log.info("RollDXTimes.process_queued_request 001")
    for times in range(request.how_many):
        log.info(f"roll number: {times} is {random.choice(numbers)}")
        await asyncio.sleep(2)
    return True
