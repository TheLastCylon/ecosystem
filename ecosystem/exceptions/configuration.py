from .exception_base import ExceptionBase


# --------------------------------------------------------------------------------
class ConfigurationExceptionBase(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)


# --------------------------------------------------------------------------------
class InstanceConfigurationNotFoundException(ConfigurationExceptionBase):
    def __init__(self, application_name: str, instance_id: str):
        super().__init__(f"Configuration for instance [{instance_id}] of application [{application_name}] not found!")
