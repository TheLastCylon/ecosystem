import uuid

from typing import Dict, List, Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..state_keepers.error_state_list import ErrorStateList


# --------------------------------------------------------------------------------
class ErrorsResponseDto(PydanticBaseModel):
    errors: List[Dict[str, Any]]


# --------------------------------------------------------------------------------
class ErrorCleanerRequestDto(PydanticBaseModel):
    error_id: str
    count   : int


# --------------------------------------------------------------------------------
def build_errors_response() -> List[Dict[str, Any]]:
    error_state_list = ErrorStateList()
    errors: List[Dict[str, Any]] = []
    for error_state in error_state_list.get_error_states():
        if error_state.is_set():
            errors.append(error_state.to_dict())
    return errors


# --------------------------------------------------------------------------------
@endpoint("eco.error_states.get")
async def eco_error_states_get(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    return ErrorsResponseDto(errors=build_errors_response())


# --------------------------------------------------------------------------------
@endpoint("eco.error_states.clear")
async def eco_error_states_clear(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    request          = cast(ErrorCleanerRequestDto, request)
    error_state_list = ErrorStateList()
    if request.count == 0:
        error_state_list.clear_all(request.error_id)
    else:
        error_state_list.clear_some(request.error_id, request.count)
    return ErrorsResponseDto(errors=build_errors_response())


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
