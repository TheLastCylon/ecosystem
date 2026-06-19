from ekosis.data_transfer_objects import EmptyDto
from ekosis.requests.endpoint import endpoint
from ekosis.data_transfer_objects import SpanKey
from ..dtos.dtos import SetupTasksRanResponseDto

# --------------------------------------------------------------------------------
# class SetupTasksRanResponseDto(PydanticBaseModel):
#     ran: bool

# Shared flag set by the background task started via setup_tasks
setup_task_ran: bool = False

# --------------------------------------------------------------------------------
@endpoint("app.c.setup_task_ran")
async def app_c_setup_task_ran(span_key: SpanKey, dto: EmptyDto) -> SetupTasksRanResponseDto:
    return SetupTasksRanResponseDto(ran=setup_task_ran)
