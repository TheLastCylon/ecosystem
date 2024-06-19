import asyncio
import random

from ecosystem.requests import QueuedRequestHandlerBase

from ..dtos import RollDXTimesRequestDto


# ---------------------------------------------
class RollDXTimes(QueuedRequestHandlerBase[RollDXTimesRequestDto]):
    def __init__(self) -> None:
        super().__init__(
            "roll_times",
            "rolls as many dice you specify, having a number of sides you specify",
            RollDXTimesRequestDto,
            "/tmp",
            0,
            0
        )

    async def process_queued_request(self, request: RollDXTimesRequestDto) -> bool:
        self.logger.info("RollDXTimes.process_queued_request 001")
        numbers = list(range(1, request.sides))
        for times in range(request.how_many):
            self.logger.info(f"roll number: {times} is {random.choice(numbers)}")
        await asyncio.sleep(2)
        return True
