from .exception_base import ExceptionBase
from ..requests.status import Status


# --------------------------------------------------------------------------------
class RoutingExceptionBase(ExceptionBase):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")


# --------------------------------------------------------------------------------
class UnknownRouteKeyException(RoutingExceptionBase):
    def __init__(self, route_key: str):
        super().__init__(Status.COMMAND_NOT_SUPPORTED.value, f"Unknown route key '{route_key}'")
