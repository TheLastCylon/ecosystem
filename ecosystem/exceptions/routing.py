from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class RoutingExceptionBase(ExceptionBase):
    def __init__(self, status: int, message: str):
        self.status: int = status
        super().__init__(f"status: [{status}] message: [{message}]")


# --------------------------------------------------------------------------------
class UnknownRouteKeyException(RoutingExceptionBase):
    def __init__(self, status: int, route_key: str):
        super().__init__(status, f"Unknown route key '{route_key}'")
