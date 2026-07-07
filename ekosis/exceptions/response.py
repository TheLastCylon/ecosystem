# --------------------------------------------------------------------------------
# These exceptions are used to indicate that the response we received from a
# server, is NOT a SUCCESS response.

from .exception_base import ExceptionBase

# --------------------------------------------------------------------------------
class ResponseException(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class ProtocolParsingException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class ClientDeniedException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class ValidationException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class RouteKeyUnknownException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class ServerBusyException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class ProcessingException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class UnhandledException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class UnknownStatusCodeException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)
