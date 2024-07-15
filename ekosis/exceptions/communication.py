from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class CommunicationExceptionBase(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
class ClientDisconnectedException(CommunicationExceptionBase):
    def __init__(self, message: str = "Client disconnected"):
        super().__init__(message)


# --------------------------------------------------------------------------------
class IncompleteMessageException(CommunicationExceptionBase):
    def __init__(self, request_str: str):
        super().__init__(f'Incomplete request received: {request_str}. Closing connection.')


# --------------------------------------------------------------------------------
class CommunicationsRetryable(CommunicationExceptionBase):
    def __init__(self, message: str = "A retryable communications failure occurred."):
        super().__init__(message)


# --------------------------------------------------------------------------------
class CommunicationsNonRetryable(CommunicationExceptionBase):
    def __init__(self, message: str = "A non-retryable communications failure occurred."):
        super().__init__(message)


# --------------------------------------------------------------------------------
class CommunicationsMaxRetriesReached(CommunicationExceptionBase):
    def __init__(self, message: str = "Maximum retries exceeded in sending request."):
        super().__init__(message)


# --------------------------------------------------------------------------------
class CommunicationsEmptyResponse(CommunicationExceptionBase):
    def __init__(self, message: str = "Empty response received."):
        super().__init__(message)
