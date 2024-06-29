from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class QueueingExceptionBase(ExceptionBase):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")


# --------------------------------------------------------------------------------
class ReceivingPausedException(QueueingExceptionBase):
    def __init__(self, status: int, route_key: str):
        super().__init__(status, f"Receiving on '{route_key}' has been paused.")
