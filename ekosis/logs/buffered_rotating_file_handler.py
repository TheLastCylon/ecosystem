from logging.handlers import RotatingFileHandler, BufferingHandler

# --------------------------------------------------------------------------------
class BufferedRotatingFileHandler(BufferingHandler):
    def __init__(
        self,
        filename,
        mode        = 'a',
        buffer_size = 0,
        max_bytes   = 0,
        backup_count= 0,
        encoding    = None,
        delay       = False,
    ):
        super().__init__(buffer_size)
        self.rotating_file_handler = RotatingFileHandler(
            filename,
            mode,
            maxBytes    = max_bytes,
            backupCount = backup_count,
            encoding    = encoding,
            delay       = delay,
        )
        self.buffer      = []
        self.buffer_size = buffer_size

    def setFormatter(self, formatter):
        self.rotating_file_handler.setFormatter(formatter)

    def flush(self):
        for record in self.buffer:
            self.rotating_file_handler.emit(record)
        self.buffer = []

    def close(self):
        self.rotating_file_handler.close()
        super().close()
