import logging
import sys

from .compressed_rotating_file_handler import CompressedRotatingFileHandler


# --------------------------------------------------------------------------------
def setup_logger(
    logging_directory   : str,
    application_name    : str,
    application_instance: str,
    max_file_size_bytes : int = (1024 * 1024), # 1 Mega-byte
    max_files           : int = 10
) -> logging.Logger:
    application_instance_name = f"{application_name}-{application_instance}"
    file_path                 = f"{logging_directory}/{application_instance_name}.log"
    logger_instance           = logging.getLogger(application_instance_name)
    date_format               = '%Y%m%d%H%M%S'
    log_format                = '%(asctime)s.%(msecs)03d|%(name)s|%(levelname)s|%(filename)s|%(lineno)s|%(message)s'
    formatter                 = logging.Formatter(log_format, datefmt=date_format)
    file_logging_handler      = CompressedRotatingFileHandler(file_path, max_bytes=max_file_size_bytes, backup_count=max_files)
    stream_logging_handler    = logging.StreamHandler(sys.stdout)

    # Set handler log level
    file_logging_handler.setLevel(logging.DEBUG)
    stream_logging_handler.setLevel(logging.INFO)

    # Set log format
    file_logging_handler.setFormatter(formatter)
    stream_logging_handler.setFormatter(formatter)

    # Set instance handlers
    logger_instance.addHandler(stream_logging_handler)
    logger_instance.addHandler(file_logging_handler)

    # Set instance log level
    logger_instance.setLevel(logging.DEBUG)

    return logger_instance
