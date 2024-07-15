# --------------------------------------------------------------------------------
# These exceptions are used to indicate that the response we received from a
# server, is NOT a SUCCESS response.

from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class ResponseException(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# PROTOCOL_PARSING_ERROR
class ProtocolParsingException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# CLIENT_DENIED
class ClientDeniedException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# PYDANTIC_VALIDATION_ERROR
class PydanticValidationException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# ROUTE_KEY_UNKNOWN
class RouteKeyUnknownException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# APPLICATION_BUSY
class ServerBusyException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# PROCESSING_FAILURE
class ProcessingException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
# UNKNOWN
class UnknownException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
class UnknownStatusCodeException(ResponseException):
    def __init__(self, message: str):
        super().__init__(message)
