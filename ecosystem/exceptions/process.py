from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class InstanceAlreadyRunningException(ExceptionBase):
    def __init__(
        self,
        application_name: str,
        instance_id     : str,
        process_id      : int
    ):
        super().__init__(f"Instance [{instance_id}] of [{application_name}] already running with process id [{process_id}]!")
