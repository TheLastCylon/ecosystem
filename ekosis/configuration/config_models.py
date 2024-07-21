import os
import sys
import json
import platform

from typing import Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field

from .argument_parser import command_line_args

from ..util.singleton import SingletonType
from ..util.utility_functions import camel_to_snake
from ..exceptions.exception_base import ExceptionBase

# --------------------------------------------------------------------------------
class ConfigurationExceptionBase(ExceptionBase):
    def __init__(self, message: str):
        super().__init__(message)

# --------------------------------------------------------------------------------
class InstanceConfigurationNotFoundException(ConfigurationExceptionBase):
    def __init__(self, name: str, instance: str):
        super().__init__(f"Configuration for instance [{instance}] of application [{name}] not found!")

# --------------------------------------------------------------------------------
application_name     = camel_to_snake(os.path.basename(sys.argv[0]).replace('.py', ''))
application_instance = command_line_args.instance
env_prefix           = "ECOENV"
env_global           = f"{env_prefix}"
env_app_name         = f"{application_name.upper()}"
env_instance         = application_instance.upper()
env_app_instance     = f"{env_app_name}_{env_instance}"

# --------------------------------------------------------------------------------
# Used for when we want to check instance, application and global default setting
# --------------------------------------------------------------------------------
def get_eco_env(postfix: str, default: Any = None, instance_level_only: bool = False):
    global env_app_instance, env_app_name, env_prefix
    global_env_name    = f"{env_prefix}_{postfix}"
    app_level_env_name = f"{global_env_name}_{env_app_name}"
    instance_env_name  = f"{app_level_env_name}_{env_instance}"
    retval: str = os.environ.get(f"{instance_env_name}") # First we try to get the value for the running instance
    if not retval:
        if instance_level_only:
            return default
        retval = os.environ.get(f"{app_level_env_name}") # Now we try to get an application level default
        if not retval:
            retval = os.environ.get(f"{global_env_name}") # And here we try to get a global default
            if not retval:
                return default # If we still don't have a value, then we return the specified default
    return retval

# --------------------------------------------------------------------------------
# Used for when only an instance level setting would be valid
# --------------------------------------------------------------------------------
def get_instance_env(postfix: str, default: Any = None):
    return get_eco_env(postfix, default, True)

# --------------------------------------------------------------------------------
def get_platform_default_dir():
    if platform.system() == "Windows":
        return get_eco_env("DEFAULT_DIR", "C:\\")
    else:
        return get_eco_env("DEFAULT_DIR", "/tmp")

platform_default_dir = get_platform_default_dir()

# ConfigStatisticsKeeper
# --------------------------------------------------------------------------------
def get_statistics_gather_period():
    # 300 seconds, i.e. 5 minutes by default
    return int(get_eco_env("STAT_GP", 300))

def get_statistics_history_length():
    # 12 by default
    # i.e. Keep an hours worth of statistics if the gather period is 300 seconds
    return int(get_eco_env("STAT_HL", 12))

class ConfigStatisticsKeeper(PydanticBaseModel):
    gather_period : int = Field(default_factory=get_statistics_gather_period)
    history_length: int = Field(default_factory=get_statistics_history_length)

# ConfigLoggingFile
# --------------------------------------------------------------------------------
def get_logfile_directory():
    return get_eco_env("LOG_DIR", platform_default_dir)

def get_logfile_base_file_name():
    return f"{application_name}-{application_instance}"

def get_logfile_base_file_path():
    return f"{get_logfile_directory()}/{get_logfile_base_file_name()}.log"

def get_buffer_size():
    # Default is no buffer. i.e. 0
    return int(get_eco_env("LOG_BUF_SIZE", 0))

def get_logfile_max_size_in_bytes():
    # (1024*1024)*10 = 10,485,760 i.e. 10 mega-bytes
    return int(get_eco_env("LOG_MAX_SIZE", 10485760))

def get_logfile_max_files():
    # 10 Files by default
    return int(get_eco_env("LOG_MAX_FILES", 10))

class ConfigLoggingFile(PydanticBaseModel):
    directory         : str  = Field(default_factory=get_logfile_directory)
    base_file_name    : str  = Field(default_factory=get_logfile_base_file_name)
    base_file_path    : str  = Field(default_factory=get_logfile_base_file_path)
    buffer_size       : int  = Field(default_factory=get_buffer_size)
    max_size_in_bytes : int  = Field(default_factory=get_logfile_max_size_in_bytes)
    max_files         : int  = Field(default_factory=get_logfile_max_files)

# ConfigLogging
# --------------------------------------------------------------------------------
def get_logging_date_format():
    return get_eco_env("LOG_DATE_FORMAT", '%Y%m%d%H%M%S') # Default to '%Y%m%d%H%M%S'

def get_logging_format():
    return get_eco_env("LOG_FORMAT", '%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s|%(lineno)d|%(message)s')

def get_logging_level():
    # List of options here: 'debug', 'info', 'warn', 'error', 'critical'
    return get_eco_env("LOG_LEVEL", 'info')

class ConfigLogging(PydanticBaseModel):
    # By default, we want both console and file logging.
    # This is because it's too easy for users to forget, that starting an
    # application in the back-ground, means the terminal can be closed and all
    # logging for the application is lost.
    # Therefore, we force the user to make a choice, and remain conscious of
    # the fact that they are making a choice.
    console_only: bool              = command_line_args.log_console_only
    file_only   : bool              = command_line_args.log_file_only
    file_logging: ConfigLoggingFile = ConfigLoggingFile()
    date_format : str               = Field(default_factory=get_logging_date_format)
    format      : str               = Field(default_factory=get_logging_format)
    level       : str               = Field(default_factory=get_logging_level)

# ConfigTCP
# --------------------------------------------------------------------------------
class ConfigTCP(PydanticBaseModel):
    host: str = "127.0.0.1"
    port: int = 8888

# ConfigUDP
# --------------------------------------------------------------------------------
class ConfigUDP(PydanticBaseModel):
    host: str = "127.0.0.1"
    port: int = 8889

# ConfigUDS
# --------------------------------------------------------------------------------
class ConfigUDS(PydanticBaseModel):
    directory       : str = "/tmp" # because we don't want sock files surviving reboot
    socket_file_name: str = "DEFAULT"

# ConfigApplicationInstance
# --------------------------------------------------------------------------------
def get_app_instance_lock_dir():
    return get_eco_env("LOCK_DIR", platform_default_dir)

def parse_host_port_string(value: str):
    # TODO: Throw an exception if we can't parse the string!
    host, port = value.split(":")
    if not host:
        return None
    if not port:
        return None
    return {
        "host": host,
        "port": int(port)
    }

def get_app_instance_tcp():
    tcp_string = get_instance_env("TCP", None)
    if tcp_string:
        host_port_data = parse_host_port_string(tcp_string)
        if host_port_data:
            return ConfigTCP(host=host_port_data["host"], port=host_port_data["port"])
    return None

def get_app_instance_udp():
    udp_string = get_instance_env("UDP", None)
    if udp_string:
        host_port_data = parse_host_port_string(udp_string)
        if host_port_data:
            return ConfigUDP(host=host_port_data["host"], port=host_port_data["port"])
    return None

def get_app_instance_uds():
    uds_string = get_instance_env("UDS", None)
    if not uds_string:
        return None
    directory        = os.path.dirname(uds_string)
    socket_file_name = os.path.basename(uds_string)
    if not directory or not socket_file_name:
        return None
    if not os.path.isdir(directory):
        return None
    if socket_file_name == "DEFAULT":
        socket_file_name = f"{application_name}_{application_instance}.uds.sock"
    return ConfigUDS(directory=directory, socket_file_name=socket_file_name)

def get_app_instance_queue_directory():
    # Do not default queue_directory to anything. Make the user explicitly set it.
    # Rather let them get an error, than lose their queues due to them having been
    # written to a place that gets cleaned on reboot.
    return get_eco_env("QUEUE_DIR", None)

def get_app_instance_extra():
    extra_env_prefix = f"{env_prefix}_EXTRA_{env_app_instance}_"
    extra_config     = {
        k: v for k, v in os.environ.items()
        if k.startswith(extra_env_prefix)
    }
    retval: Dict[str, Any] = {}
    for key in extra_config.keys():
        new_key = key.replace(extra_env_prefix, "")
        retval[new_key] = extra_config[key]
    return retval

class ConfigApplicationInstance(PydanticBaseModel):
    application_name: str                    = application_name
    instance_id     : str                    = application_instance
    stats_keeper    : ConfigStatisticsKeeper = ConfigStatisticsKeeper()
    logging         : ConfigLogging          = ConfigLogging()
    lock_directory  : str                    = Field(default_factory=get_app_instance_lock_dir)
    tcp             : ConfigTCP              = Field(default_factory=get_app_instance_tcp)
    udp             : ConfigUDP              = Field(default_factory=get_app_instance_udp)
    uds             : ConfigUDS              = Field(default_factory=get_app_instance_uds)
    queue_directory : str                    = Field(default_factory=get_app_instance_queue_directory)
    extra           : Any                    = Field(default_factory=get_app_instance_extra)

# ConfigApplicationInstanceDefaults
# --------------------------------------------------------------------------------
class ConfigApplicationInstanceDefaults(PydanticBaseModel):
    lock_directory  : str                    = Field(default_factory=get_app_instance_lock_dir)
    logging         : ConfigLogging          = ConfigLogging()
    stats_keeper    : ConfigStatisticsKeeper = ConfigStatisticsKeeper()
    queue_directory : str                    = Field(default_factory=get_app_instance_queue_directory)
    extra           : Any                    = None

# ConfigApplication
# --------------------------------------------------------------------------------
class ConfigApplication(PydanticBaseModel):
    name             : str                                  = application_name
    running_instance : str                                  = application_instance
    instances        : Dict[str, ConfigApplicationInstance] = {application_instance: ConfigApplicationInstance()}
    instance_defaults: ConfigApplicationInstanceDefaults    = ConfigApplicationInstanceDefaults()

# If a configuration file was specified, load the config from there.
# --------------------------------------------------------------------------------
try:
    if command_line_args.config_file:
        file_path = command_line_args.config_file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The specified configuration file [{file_path}] does NOT exist.")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The specified configuration file [{file_path}] is NOT a file.")

        with open(file_path, 'r') as f:
            config_json = json.load(f)

        application_configuration = ConfigApplication(**config_json)
    else:
        application_configuration = ConfigApplication()
except Exception as e:
    print(str(e))
    sys.exit(1)

if application_instance not in application_configuration.instances.keys():
    # When loading from environment, this isn't even be possible.
    # It's here because loading configurations from file, could have this happen.
    print(f"Configuration for instance [{application_instance}] of application [{application_name}] not found!")
    sys.exit(2)

instance_configuration = application_configuration.instances[application_instance]

# --------------------------------------------------------------------------------
class AppConfiguration(metaclass=SingletonType):
    name             = application_name
    instance         = application_instance
    tcp              = instance_configuration.tcp
    udp              = instance_configuration.udp
    uds              = instance_configuration.uds
    stats_keeper     = instance_configuration.stats_keeper
    logging          = instance_configuration.logging
    lock_directory   = instance_configuration.lock_directory
    queue_directory  = instance_configuration.queue_directory
    extra            = instance_configuration.extra

    def dict(self):
        return {
            "name"           : self.name,
            "instance"       : self.instance,
            "tcp"            : None if self.tcp is None else self.tcp.model_dump(),
            "udp"            : None if self.udp is None else self.udp.model_dump(),
            "uds"            : None if self.uds is None else self.uds.model_dump(),
            "stats_keeper"   : self.stats_keeper.model_dump(),
            "logging"        : self.logging.model_dump(),
            "lock_directory" : self.lock_directory,
            "queue_directory": self.queue_directory,
            "extra"          : self.extra,
        }
