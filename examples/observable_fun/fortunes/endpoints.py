import os
import sys
import random
import logging

from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.data_transfer_objects import SpanKey

from .dtos import FortuneResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
directory     = os.path.dirname(sys.argv[0])
filename      = 'data.txt'
filepath      = f"{directory}/{filename}"
fortune_lines = []

# --------------------------------------------------------------------------------
with open(filepath, 'r') as f:
    while True:
        line = f.readline()
        if not line:
            break
        fortune_lines.append(line.strip())

# --------------------------------------------------------------------------------
@endpoint("app.get_fortune")
async def get_fortune(span_key: SpanKey) -> PydanticBaseModel:
    log.info(f"RCV: span_key[{span_key}]")
    return FortuneResponseDto(fortune=random.choice(fortune_lines))
