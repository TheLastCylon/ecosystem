import os
import gzip
from logging.handlers import RotatingFileHandler


# --------------------------------------------------------------------------------
class CompressedRotatingFileHandler(RotatingFileHandler):
    """
    Handler for logs to a set of files, which switches from one file
    to the next when the current file reaches a certain size. Upon switching,
    the file that was being logged to, is compressed using gzip compression.

    Derived from: Python's logs.handlers.RotatingFileHandler
    """
    def __init__(
        self,
        file_path   : str,
        max_bytes   : int        = 0,
        backup_count: int        = 0,
        encoding    : str | None = None,
        delay       : bool       = False
    ):
        """
        Attributes:
            file_path (str)   : The path to the log file
            max_bytes (int)   : The maximum size of the log file, before rotating it
            backup_count (int): The number of compressed log files to keep
            encoding (str)    : is the name of the encoding used to decode or encode the log file. See documentation for open(), for more detail
            delay (bool)      : If True, the log file is not created/opened until the first log message is emitted.

        Open the specified file_path and use it as the stream for logs.

        If `max_bytes` is set to 0, the file specified grows indefinitely. i.e. rollover
        never happens.

        Specifying values for `max_bytes` and `backup_count`, will cause rollover of
        the file when it's size approaches max_bytes.

        Rollover occurs when the file currently being logged to, nears max_bytes
        in size. When backup_count is set to a positive, non-zero value, the system
        will create new files with the name specified in file_path, having extensions
        ".1.gz", ".2.gz" etc. appended.

        e.g. With backup_count at 5 and a ekosis file name of "app.log", you would get
        "app.log",
        "app.log.1.gz",
        "app.log.2.gz", ... to "app.log.5.gz".

        "app.log" is always the file being written to.
        When it gets filled up, it is closed, compressed and renamed to "app.log.1.gz".
        If files "app.log.1", "app.log.2" etc. exist, then they are renamed to "app.log.2", "app.log.3" etc.
        """
        self.file_path                 = file_path
        self.counter_width             = len(str(backup_count))+1
        self.compressed_file_extension = "gz"
        super(CompressedRotatingFileHandler, self).__init__(
                self.file_path,
                maxBytes   = max_bytes,
                backupCount= backup_count,
                encoding   = encoding,
                delay      = delay
        )

    def compressed_file_name(self, number: int) -> str:
        return f"{self.baseFilename}.{str(number).rjust(self.counter_width, '0')}.{self.compressed_file_extension}"

    @staticmethod
    def compress_file(source_file_name: str, destination_file_name: str) -> None:
        with open(source_file_name, 'rb') as source_file, \
             gzip.open(destination_file_name, 'wb') as destination_file:
            destination_file.writelines(source_file)

    # Override the ekosis doRollover method because we want to add compression to this.
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount-1, 0, -1):
                source_file_name      = self.compressed_file_name(i)
                destination_file_name = self.compressed_file_name(i+1)
                if os.path.exists(source_file_name):
                    os.rename(source_file_name, destination_file_name)
            self.compress_file(self.baseFilename, self.compressed_file_name(1))
            os.remove(self.baseFilename)

        if not self.delay:
            self.stream = self._open()
