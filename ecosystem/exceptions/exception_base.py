# --------------------------------------------------------------------------------
class ExceptionBase(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{type(self).__name__}: {self.message}"
