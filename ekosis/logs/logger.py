import logging
import sys

from .buffered_rotating_file_handler import BufferedRotatingFileHandler

from ..configuration.config_models import AppConfiguration, ConfigLogging
from ..util import SingletonType

# --------------------------------------------------------------------------------
class EcoLogger(metaclass=SingletonType):
    __app_config        : AppConfiguration            = AppConfiguration()
    __log_config        : ConfigLogging               = __app_config.logging
    __level             : int                         = logging.DEBUG
    __logger            : logging.Logger              = None
    __formatter         : logging.Formatter           = None
    __file_handler      : BufferedRotatingFileHandler = None
    __console_handler                                 = None

    # --------------------------------------------------------------------------------
    def __setup_file_logging(self):
        log_file_config = self.__log_config.file_logging
        self.__file_handler = BufferedRotatingFileHandler(
            log_file_config.base_file_path,
            buffer_size  = log_file_config.buffer_size,
            max_bytes    = log_file_config.max_size_in_bytes,
            backup_count = log_file_config.max_files
        )

        self.__file_handler.setLevel(self.__level)
        self.__file_handler.setFormatter(self.__formatter)
        self.__logger.addHandler(self.__file_handler)

    # --------------------------------------------------------------------------------
    def __setup_console_logging(self):
        self.__console_handler = logging.StreamHandler(sys.stdout)
        self.__console_handler.setLevel(self.__level)
        self.__console_handler.setFormatter(self.__formatter)
        self.__logger.addHandler(self.__console_handler)

    # --------------------------------------------------------------------------------
    def __set_level(self, level: int):
        self.__level = level

        if self.__file_handler:
            self.__file_handler.setLevel(level)

        if self.__console_handler:
            self.__console_handler.setLevel(level)

        self.__logger.setLevel(level)

    # --------------------------------------------------------------------------------
    def set_level(self, level: str):
        if level == 'debug':
            self.__set_level(logging.DEBUG)

        if level == 'info':
            self.__set_level(logging.INFO)

        if level == 'warn':
            self.__set_level(logging.WARNING)

        if level == 'error':
            self.__set_level(logging.ERROR)

        if level == 'critical':
            self.__set_level(logging.CRITICAL)

    # --------------------------------------------------------------------------------
    def setup(self):
        log_file_config                = self.__log_config.file_logging
        log_file_config.base_file_name = f"{self.__app_config.name}-{self.__app_config.instance}"
        log_file_config.base_file_path = f"{log_file_config.directory}/{log_file_config.base_file_name}.log"
        self.__logger                  = logging.getLogger() # Yes, we are configuring the root logger!
        self.__formatter               = logging.Formatter(self.__log_config.format, datefmt=self.__log_config.date_format)

        if not self.__log_config.console_only:
            self.__setup_file_logging()

        if not self.__log_config.file_only:
            self.__setup_console_logging()

        self.__logger.setLevel(self.__level)
        # This switches asyncio logging to level WARNING
        # logging.getLogger('asyncio').setLevel(logging.WARNING)

    # --------------------------------------------------------------------------------
    def flush(self):
        if not self.__log_config.file_only:
            self.__console_handler.flush()

        if not self.__log_config.console_only:
            self.__file_handler.flush()

# --------------------------------------------------------------------------------
ekosis_logger = EcoLogger()
ekosis_logger.setup()
