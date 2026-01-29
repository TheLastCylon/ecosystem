from ekosis.sending.sender import sender
from ekosis.sending.buffered_sender import buffered_sender
from ekosis.data_transfer_objects import EmptyDto, BufferedEndpointResponseDTO

from ..fortunes.dtos import FortuneResponseDto
from ..joker.dtos import JokerResponseDto
from ..lottery.dtos import NumberPickerRequestDto, NumberPickerResponseDto
from ..magic_eight_ball.dtos import Magic8BallRequestDto, Magic8BallResponseDto
from ..time_reporter.dtos import CurrentTimeResponseDto
from ..tracker.dtos import TrackerLogRequestDto

from .clients import (
    fortunes_client,
    joker_client,
    lottery_client,
    magic8ball_client,
    time_reporter_client,
    tracker_client
)


# --------------------------------------------------------------------------------
@sender(fortunes_client, "app.get_fortune", FortuneResponseDto)
async def get_fortune(*args, **kwargs):
    return EmptyDto()


# --------------------------------------------------------------------------------
@sender(joker_client, "app.get_joke", JokerResponseDto)
async def get_joke(*args, **kwargs):
    return EmptyDto()


# --------------------------------------------------------------------------------
@sender(lottery_client, "app.pick_numbers", NumberPickerResponseDto)
async def pick_numbers(how_many: int = 1, *args, **kwargs):
    return NumberPickerRequestDto(how_many=how_many)


# --------------------------------------------------------------------------------
@sender(magic8ball_client, "app.get_prediction", Magic8BallResponseDto)
async def get_prediction(question: str, *args, **kwargs):
    return Magic8BallRequestDto(question=question)


# --------------------------------------------------------------------------------
@sender(time_reporter_client, "app.get_time", CurrentTimeResponseDto)
async def get_time(*args, **kwargs):
    return EmptyDto()


# --------------------------------------------------------------------------------
@buffered_sender(
    tracker_client,
    "app.log_request",
    TrackerLogRequestDto,
    BufferedEndpointResponseDTO,
    0,
    100,
    10
)
async def log_request(data: str, timestamp: float, *args, **kwargs):
    return TrackerLogRequestDto(
        request   = data,
        timestamp = timestamp
    )


# --------------------------------------------------------------------------------
@buffered_sender(
    tracker_client,
    "app.log_response",
    TrackerLogRequestDto,
    BufferedEndpointResponseDTO,
    0,
    100,
    10
)
async def log_response(data: str, timestamp: float, *args, **kwargs):
    return TrackerLogRequestDto(
        request   = data,
        timestamp = timestamp
    )
