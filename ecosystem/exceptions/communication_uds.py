from .communication import CommunicationsRetryable
from .communication import CommunicationsNonRetryable
from .communication import CommunicationsMaxRetriesReached
from .communication import CommunicationsEmptyResponse


# --------------------------------------------------------------------------------
class UDSCommunicationsFailureRetryable(CommunicationsRetryable):
    def __init__(self, path: str, message: str):
        super().__init__(f"Retryable communications failure in request to host [{path}]: {message}")


# --------------------------------------------------------------------------------
class UDSCommunicationsFailureNonRetryable(CommunicationsNonRetryable):
    def __init__(self, path: str, message: str):
        super().__init__(f"Non-Retryable error in request to host [{path}]: {message}")


# --------------------------------------------------------------------------------
class UDSCommunicationsFailureMaxRetriesReached(CommunicationsMaxRetriesReached):
    def __init__(self, path: str):
        super().__init__(f"Request to host [{path}] failed too many times")


# --------------------------------------------------------------------------------
class UDSCommunicationsFailureEmptyResponse(CommunicationsEmptyResponse):
    def __init__(self, path: str):
        super().__init__(f"Received empty response from host [{path}]")
