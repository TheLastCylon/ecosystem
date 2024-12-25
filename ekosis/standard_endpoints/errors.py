from typing import Dict, List, Any
from pydantic import BaseModel as PydanticBaseModel

from ..requests.endpoint import endpoint
from ..state_keepers.error_state_list import ErrorStateList
from ..data_transfer_objects import ErrorsResponseDto, ErrorCleanerRequestDto, EmptyDto

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
async def eco_error_states_get(dto: EmptyDto, **kwargs) -> PydanticBaseModel:
    return ErrorsResponseDto(errors=build_errors_response())

# --------------------------------------------------------------------------------
@endpoint("eco.error_states.clear", ErrorCleanerRequestDto)
async def eco_error_states_clear(dto: ErrorCleanerRequestDto, **kwargs) -> PydanticBaseModel:
    error_state_list = ErrorStateList()
    if error_state_list.has_error_id(dto.error_id):
        if dto.count == 0:
            error_state_list.clear_all(dto.error_id)
        else:
            error_state_list.clear_some(dto.error_id, dto.count)
    return ErrorsResponseDto(errors=build_errors_response())
