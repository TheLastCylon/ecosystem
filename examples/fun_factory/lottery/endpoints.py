import uuid
import random
import logging

from typing import List
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint

from .dtos import NumberPickerRequestDto, NumberPickerResponseDto

log = logging.getLogger()


# --------------------------------------------------------------------------------
def pick_number_set() -> str:
    numbers      : List[int] = list(range(1, 52))
    choices      : List[int] = []
    line_to_print: str       = ""
    first        : bool      = True

    for i in range(0, 7):
        choice = random.choice(numbers)
        choices.append(choice)
        numbers.remove(choice)

    selection = choices[0:6]
    selection.sort()

    for i in selection:
        if first:
            first = False
        else:
            line_to_print += ", "
        line_to_print += f"{str(i).rjust(2, ' ')}"

    line_to_print += f" [{str(choices[6]).rjust(2, ' ')}]"

    return line_to_print


# --------------------------------------------------------------------------------
def pick_numbers(how_many: int) -> List[str]:
    lotto_numbers: List[str] = []
    for j in range(how_many):
        lotto_numbers.append(pick_number_set())
    return lotto_numbers


# --------------------------------------------------------------------------------
@endpoint("app.pick_numbers", NumberPickerRequestDto)
async def pick_numbers_endpoint(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    log.info(f"RCV: request_uuid[{request_uuid}]")
    return NumberPickerResponseDto(numbers=pick_numbers(request.how_many))
