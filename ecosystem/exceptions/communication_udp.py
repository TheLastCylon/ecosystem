from .communication import CommunicationsRetryable
from .communication import CommunicationsNonRetryable
from .communication import CommunicationsMaxRetriesReached
from .communication import CommunicationsEmptyResponse


# --------------------------------------------------------------------------------
class UDPCommunicationsFailureRetryable(CommunicationsRetryable):
    def __init__(self, host: str, port: int, message: str):
        super().__init__(f"Retryable communications failure in request to host [{host}] on port [{port}]: {message}")


# --------------------------------------------------------------------------------
class UDPCommunicationsFailureNonRetryable(CommunicationsNonRetryable):
    def __init__(self, host: str, port: int, message: str):
        super().__init__(f"Non-Retryable error in request to host [{host}] on port [{port}]: {message}")


# --------------------------------------------------------------------------------
class UDPCommunicationsFailureMaxRetriesReached(CommunicationsMaxRetriesReached):
    def __init__(self, host: str, port: int):
        super().__init__(f"Request to host [{host}] on port [{port}] failed too many times")


# --------------------------------------------------------------------------------
class UDPCommunicationsFailureEmptyResponse(CommunicationsEmptyResponse):
    def __init__(self, host: str, port: int):
        super().__init__(f"Received empty response from host [{host}] on port [{port}]")
