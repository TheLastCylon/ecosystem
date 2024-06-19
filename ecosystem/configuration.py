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
    socket_file_name: str = "use_default"


# --------------------------------------------------------------------------------
class ConfigApplicationInstance(PydanticBaseModel):
    instance_id : str                           = "0"
    tcp         : ConfigTCP              = None
    udp         : ConfigUDP              = None
    uds         : ConfigUDS              = None
    stats_keeper: ConfigStatisticsKeeper = ConfigStatisticsKeeper()
    logging     : ConfigLogging          = ConfigLogging()


# --------------------------------------------------------------------------------
class ConfigAppDefaults(PydanticBaseModel):
    tcp         : ConfigTCP              = None
    udp         : ConfigUDP              = None
    uds         : ConfigUDS              = None
    logging     : ConfigLogging          = ConfigLogging()
    stats_keeper: ConfigStatisticsKeeper = ConfigStatisticsKeeper()


# --------------------------------------------------------------------------------
class ConfigApplication(PydanticBaseModel):
    name     : str
    defaults : ConfigAppDefaults                    = ConfigAppDefaults()
    instances: Dict[str, ConfigApplicationInstance] = {"0": ConfigApplicationInstance()}


# --------------------------------------------------------------------------------
class ConfigSystem(PydanticBaseModel):
    applications: Dict[str, ConfigApplication]


app_config = ConfigApplication(
    name     = "base",
    defaults = ConfigAppDefaults(
        tcp          = ConfigTCP(host = "127.0.0.1", port = 8888),
        udp          = ConfigUDP(host = "127.0.0.1", port = 8889),
        uds          = ConfigUDS(directory = "/tmp", socket_file_name = "use_default"),
        logging      = ConfigLogging(directory = "/tmp", max_size_in_bytes = 10737418240, max_files = 10),
        stats_keeper = ConfigStatisticsKeeper(gather_period = 300, history_length = 12),
    ),
    instances = {
        "0": ConfigApplicationInstance(
            instance_id  = "0",
            tcp          = ConfigTCP(host = "127.0.0.1", port = 8888),
            udp          = ConfigUDP(host = "127.0.0.1", port = 8889),
            uds          = ConfigUDS(directory = "/tmp", socket_file_name = "use_default"),
            stats_keeper = ConfigStatisticsKeeper(gather_period = 300, history_length = 12),
            logging      = ConfigLogging(directory = "/tmp", max_size_in_bytes = 10737418240, max_files = 10),
        )
    },
)


system_config = ConfigSystem(
    applications = {
        "base": app_config,
    }
)

print(system_config.json())
