import logging
import sys

from .compressed_rotating_file_handler import CompressedRotatingFileHandler
from ..util import SingletonType
from ..configuration import ConfigLogging


# --------------------------------------------------------------------------------
class EcoLogger(metaclass=SingletonType):
    __date_format    : str                           = '%Y%m%d%H%M%S'
    __log_format     : str                           = '%(asctime)s.%(msecs)03d|%(name)s|%(levelname)s|%(filename)s|%(lineno)s|%(message)s'
    __logger_name    : str                           = None
    __file_path      : str                           = None
    __level          : int                           = logging.DEBUG
    __logger         : logging.Logger                = None
    __formatter      : logging.Formatter             = None
    __file_handler   : CompressedRotatingFileHandler = None
    __console_handler                                = None

    def __init__(self):
        pass

    def debug(self, message: str):
        if self.__logger:
            self.__logger.debug(message)

    def info(self, message: str):
        if self.__logger:
            self.__logger.info(message)

    def warn(self, message: str):
        if self.__logger:
            self.__logger.warning(message)

    def error(self, message: str):
        if self.__logger:
            self.__logger.error(message)

    def __setup_file_logging(self, file_path: str, max_bytes: int, max_files: int):
        self.__file_handler = CompressedRotatingFileHandler(
            file_path,
            max_bytes    = max_bytes,
            backup_count = max_files
        )
        self.__file_handler.setLevel(self.__level)
        self.__file_handler.setFormatter(self.__formatter)
        self.__logger.addHandler(self.__file_handler)

    def __setup_console_logging(self):
        self.__console_handler = logging.StreamHandler(sys.stdout)
        self.__console_handler.setLevel(self.__level)
        self.__console_handler.setFormatter(self.__formatter)
        self.__logger.addHandler(self.__console_handler)

    def __set_level(self, level: int):
        if self.__file_handler:
            self.__file_handler.setLevel(level)

        if self.__console_handler:
            self.__console_handler.setLevel(level)

        self.__logger.setLevel(level)

    def set_level(self, level: str):
        if level == 'debug':
            self.__set_level(logging.DEBUG)

        if level == 'info':
            self.__set_level(logging.INFO)

        if level == 'warn':
            self.__set_level(logging.WARNING)

        if level == 'error':
            self.__set_level(logging.ERROR)

    def setup(
        self,
        application_name    : str,
        application_instance: str,
        configuration       : ConfigLogging,
        log_to_file         : bool = True,
        log_to_console      : bool = True,
    ):
        self.__logger_name = f"{application_name}-{application_instance}"
        self.__file_path   = f"{configuration.directory}/{self.__logger_name}.log"
        self.__logger      = logging.getLogger(self.__logger_name)
        self.__formatter   = logging.Formatter(self.__log_format, datefmt=self.__date_format)

        if log_to_file:
            self.__setup_file_logging(
                self.__file_path,
                configuration.max_size_in_bytes,
                configuration.max_files
            )

        if log_to_console:
            self.__setup_console_logging()

        self.__logger.setLevel(self.__level)


# --------------------------------------------------------------------------------
# def setup_logger(
#     application_name    : str,
#     application_instance: str,
#     configuration       : ConfigLogging,
#
# ) -> logging.Logger:
#     application_instance_name = f"{application_name}-{application_instance}"
#     file_path                 = f"{configuration.directory}/{application_instance_name}.log"
#     logger_instance           = logging.getLogger(application_instance_name)
#     date_format               = '%Y%m%d%H%M%S'
#     log_format                = '%(asctime)s.%(msecs)03d|%(name)s|%(levelname)s|%(filename)s|%(lineno)s|%(message)s'
#     formatter                 = logging.Formatter(log_format, datefmt=date_format)
#     stream_logging_handler    = logging.StreamHandler(sys.stdout)
#     file_logging_handler      = CompressedRotatingFileHandler(
#         file_path,
#         max_bytes    = configuration.max_size_in_bytes,
#         backup_count = configuration.max_files
#     )
#
#     # Set handler log level
#     file_logging_handler.setLevel(logging.DEBUG)
#     stream_logging_handler.setLevel(logging.INFO)
#
#     # Set log format
#     file_logging_handler.setFormatter(formatter)
#     stream_logging_handler.setFormatter(formatter)
#
#     # Set instance handlers
#     logger_instance.addHandler(stream_logging_handler)
#     logger_instance.addHandler(file_logging_handler)
#
#     # Set instance log level
#     logger_instance.setLevel(logging.DEBUG)
#
#     return logger_instance
