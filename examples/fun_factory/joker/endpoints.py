import os
import sys
import uuid
import random
import logging

from pydantic import BaseModel as PydanticBaseModel

from ecosystem.requests.endpoint import endpoint

from .dtos import JokerResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
directory  = os.path.dirname(sys.argv[0])
filename   = 'dad_jokes.txt'
filepath   = f"{directory}/{filename}"
joke_lines = []

with open(filepath, 'r') as f:
    while True:
        line = f.readline()
        if not line:
            break
        joke_lines.append(line.strip())


# --------------------------------------------------------------------------------
@endpoint("app.get_joke")
async def get_joke(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    log.info(f"RCV: request_uuid[{request_uuid}]")
    return JokerResponseDto(joke=random.choice(joke_lines))
