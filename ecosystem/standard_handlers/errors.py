import uuid

from typing import Dict, List, Any, cast
from pydantic import BaseModel as PydanticBaseModel

from ..requests import HandlerBase
from ..state_keepers.error_state_keeper import ErrorStateKeeper
from ..state_keepers.error_state_list import ErrorStateList


# --------------------------------------------------------------------------------
class ErrorsResponseDto(PydanticBaseModel):
    errors: List[Dict[str, Any]]


# --------------------------------------------------------------------------------
class ErrorCleanerRequestDto(PydanticBaseModel):
    error_id: str
    count   : int


# --------------------------------------------------------------------------------
def build_errors_response(error_list: List[ErrorStateKeeper]) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    for error_state in error_list:
        if error_state.is_set():
            errors.append(error_state.to_dict())
    return errors


# --------------------------------------------------------------------------------
class ErrorReporter(HandlerBase):
    def __init__(self) -> None:
        super(ErrorReporter, self).__init__(
            "eco-error-states",
            "retrieves the application error states"
        )
        self.error_state_list : ErrorStateList = ErrorStateList()

    async def run(self, request_uuid: uuid.UUID, request) -> PydanticBaseModel:
        return ErrorsResponseDto(errors=build_errors_response(self.error_state_list.get_error_states()))


# --------------------------------------------------------------------------------
class ErrorCleaner(HandlerBase):
    def __init__(self) -> None:
        super(ErrorCleaner, self).__init__(
            "eco-error-clear",
            "used to mark an application error state as cleared",
            ErrorCleanerRequestDto
        )
        self.error_state_list : ErrorStateList = ErrorStateList()

    async def run(self, request_uuid: uuid.UUID, request) -> PydanticBaseModel:
        request = cast(ErrorCleanerRequestDto, request)
        if request.count == 0:
            self.error_state_list.clear_all(request.error_id)
        else:
            self.error_state_list.clear_some(request.error_id, request.count)

        return ErrorsResponseDto(errors=build_errors_response(self.error_state_list.get_error_states()))


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
