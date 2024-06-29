import os
import sys

from .config_models import ConfigApplication
from .loaders import load_config_from_file, load_config_from_environment
from .argument_parser import command_line_args

from ..util.singleton import SingletonType
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
application_name = os.path.basename(sys.argv[0]).replace('.py', '')

if not command_line_args.instance:
    application_instance = "0"
else:
    application_instance = command_line_args.instance

application_configuration: ConfigApplication = None

if command_line_args.config_file:
    application_configuration = load_config_from_file(command_line_args.config_file)
else:
    application_configuration = load_config_from_environment(application_name, application_instance)

if application_instance not in application_configuration.instances.keys():
    # When loading from environment, this should not even be possible.
    # It's here because loading configurations from file, could have this happen.
    raise InstanceConfigurationNotFoundException(application_name, application_instance)

instance_configuration                      = application_configuration.instances[application_instance]
instance_configuration.application_name     = application_name
instance_configuration.logging.console_only = command_line_args.log_console_only
instance_configuration.logging.file_only    = command_line_args.log_file_only


class AppConfiguration(metaclass=SingletonType):
    name             = instance_configuration.application_name
    instance         = instance_configuration.instance_id
    tcp              = instance_configuration.tcp
    udp              = instance_configuration.udp
    uds              = instance_configuration.uds
    stats_keeper     = instance_configuration.stats_keeper
    logging          = instance_configuration.logging
    lock_directory   = instance_configuration.lock_directory
    queue_directory  = instance_configuration.queue_directory
