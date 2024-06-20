import json

from typing import Dict
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class ConfigStatisticsKeeper(PydanticBaseModel):
    gather_period : int = 300
    history_length: int = 12


# --------------------------------------------------------------------------------
class ConfigLogging(PydanticBaseModel):
    directory        : str = "/tmp"
    max_size_in_bytes: int = 10737418240, # (1024*1024*1024)*10 = 10,737,418,240 i.e. 10 mega-bytes
    max_files        : int = 10


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
    directory       : str = "/tmp"
    socket_file_name: str = "DEFAULT"


# --------------------------------------------------------------------------------
class ConfigApplicationInstance(PydanticBaseModel):
    instance_id : str                    = "0"
    tcp         : ConfigTCP              = None
    udp         : ConfigUDP              = None
    uds         : ConfigUDS              = None
    stats_keeper: ConfigStatisticsKeeper = ConfigStatisticsKeeper()
    logging     : ConfigLogging          = ConfigLogging()


# --------------------------------------------------------------------------------
class ConfigApplication(PydanticBaseModel):
    name     : str
    instances: Dict[str, ConfigApplicationInstance] = {}
