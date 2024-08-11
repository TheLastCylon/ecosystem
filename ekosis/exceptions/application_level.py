from .exception_base import ExceptionBase

# --------------------------------------------------------------------------------
class ApplicationProcessingException(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)
