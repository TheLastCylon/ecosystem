import uuid
import random
import logging

from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests import endpoint

from .dtos import Magic8BallRequestDto, Magic8BallResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
possible_responses = [
    'It is certain!',
    'It is decidedly so!',
    'Without a doubt!',
    'Yes definitely!',
    'You may rely on it!',
    'As I see it, yes.',
    'Most likely.',
    'Outlook good.',
    'Yes.',
    'Signs point to yes.',
    'Reply hazy, try again.',
    'Ask again later.',
    'Better not tell you now.',
    'Cannot predict now.',
    'Concentrate and ask again.',
    'Don\'t count on it!',
    'My reply is: "No!"',
    'My sources say: "No!"',
    'Outlook not so good.',
    'Very doubtful.'
]


# --------------------------------------------------------------------------------
@endpoint("app.get_prediction", Magic8BallRequestDto)
async def get_prediction(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    log.info(f"RCV: request_uuid[{request_uuid}]")
    return Magic8BallResponseDto(prediction=random.choice(possible_responses))
