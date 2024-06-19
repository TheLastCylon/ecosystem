from .communication import CommunicationsRetryable
from .communication import CommunicationsNonRetryable
from .communication import CommunicationsMaxRetriesReached
from .communication import CommunicationsEmptyResponse


# --------------------------------------------------------------------------------
class TCPCommunicationsFailureRetryable(CommunicationsRetryable):
    def __init__(self, host: str, port: int, message: str):
        super().__init__(f"Retryable communications failure in request to host [{host}] on port [{port}]: {message}")


# --------------------------------------------------------------------------------
class TCPCommunicationsFailureNonRetryable(CommunicationsNonRetryable):
    def __init__(self, host: str, port: int, message: str):
        super().__init__(f"Non-Retryable error in request to host [{host}] on port [{port}]: {message}")


# --------------------------------------------------------------------------------
class TCPCommunicationsFailureMaxRetriesReached(CommunicationsMaxRetriesReached):
    def __init__(self, host: str, port: int):
        super().__init__(f"Request to host [{host}] on port [{port}] failed too many times")


# --------------------------------------------------------------------------------
class TCPCommunicationsFailureEmptyResponse(CommunicationsEmptyResponse):
    def __init__(self, host: str, port: int):
        super().__init__(f"Received empty response from host [{host}] on port [{port}]")
