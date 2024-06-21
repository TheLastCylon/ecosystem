from .exception_base import ExceptionBase
from ..requests.status import Status


# --------------------------------------------------------------------------------
class QueueingExceptionBase(ExceptionBase):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")


# --------------------------------------------------------------------------------
class ReceivingPausedException(QueueingExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.APPLICATION_BUSY.value, f"Receiving on '{route_key}' has been paused.")
