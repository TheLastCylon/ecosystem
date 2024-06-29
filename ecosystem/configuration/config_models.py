import json

from typing import Dict
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class ConfigStatisticsKeeper(PydanticBaseModel):
    gather_period : int = 300
    history_length: int = 12


# --------------------------------------------------------------------------------
class ConfigLoggingFile(PydanticBaseModel):
    directory         : str  = "/tmp"
    base_file_name    : str  = "ecosystem_default"
    base_file_path    : str  = f"{directory}/{base_file_name}.log"
    do_compression    : bool = False
    max_size_in_bytes : int  = 10737418240 # (1024*1024*1024)*10 = 10,737,418,240 i.e. 10 mega-bytes
    max_files         : int  = 10


# --------------------------------------------------------------------------------
class ConfigLogging(PydanticBaseModel):
    # By default, we want both console and file logging.
    # This is because it's too easy for users to forget, that starting an
    # application in the back-ground, means the terminal can be closed and all
    # logging for the application is lost.
    # Therefore, we force the user to make a choice, and remain conscious of
    # the fact that they are making a choice.
    console_only: bool              = False
    file_only   : bool              = False
    file_logging: ConfigLoggingFile = ConfigLoggingFile()
    date_format : str               = '%Y%m%d%H%M%S'
    format      : str               = '%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s|%(lineno)d|%(message)s'
    level       : str               = 'debug' # Other options are:


# --------------------------------------------------------------------------------
class ConfigTCP(PydanticBaseModel):
    host: str = "127.0.0.1"
    port: int = 8888


# --------------------------------------------------------------------------------
class ConfigUDP(PydanticBaseModel):
    host: str = "127.0.0.1"
    port: int = 8889


# --------------------------------------------------------------------------------
class ConfigUDS(PydanticBaseModel):
    directory       : str = "/tmp" # because we don't want sock files surviving reboot
    socket_file_name: str = "DEFAULT"


# --------------------------------------------------------------------------------
class ConfigApplicationInstance(PydanticBaseModel):
    application_name: str                    = None
    instance_id     : str                    = "0"
    tcp             : ConfigTCP              = None
    udp             : ConfigUDP              = None
    uds             : ConfigUDS              = None
    stats_keeper    : ConfigStatisticsKeeper = ConfigStatisticsKeeper()
    logging         : ConfigLogging          = ConfigLogging()
    lock_directory  : str                    = "/tmp"
    # Do not default queue_directory to anything. Make the user explicitly set it.
    # Rather let them get an error, than lose their queues due to them having been
    # written to a place that gets cleaned on reboot.
    queue_directory : str                    = None


# --------------------------------------------------------------------------------
class ConfigApplication(PydanticBaseModel):
    name            : str
    instances       : Dict[str, ConfigApplicationInstance] = {}
    running_instance: str
