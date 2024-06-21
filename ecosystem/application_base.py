import asyncio
import argparse

from .logs import EcoLogger

from .requests import HandlerBase
from .requests import RequestRouter

from .servers import TCPServer
from .servers import UDPServer
from .servers import UDSServer

from .state_keepers import ErrorStateList
from .state_keepers import StatisticsKeeper

from .configuration import ConfigApplication
from .configuration import load_config_from_file
from .configuration import load_config_from_environment

from .util import SingletonType

from .exceptions import InstanceConfigurationNotFoundException

from .standard_endpoints import standard_endpoint_error_states # noqa
from .standard_endpoints import standard_endpoint_error_clear  # noqa
from .standard_endpoints import standard_endpoint_statistics   # noqa


# --------------------------------------------------------------------------------
class ApplicationBase(metaclass=SingletonType):
    argument_parser       : argparse.ArgumentParser = argparse.ArgumentParser()
    command_line_args     : argparse.Namespace      = None
    logger                : EcoLogger               = EcoLogger()
    __request_router      : RequestRouter           = RequestRouter()
    __statistics_keeper   : StatisticsKeeper        = StatisticsKeeper()
    __error_state_list    : ErrorStateList          = ErrorStateList()
    __running             : bool                    = False
    __configuration       : ConfigApplication       = None
    __application_name    : str                     = None
    __application_instance: str                     = None
    __server_tcp          : TCPServer               = None
    __server_udp          : UDPServer               = None
    __server_uds          : UDSServer               = None

    def __init__(self, name: str, configuration: ConfigApplication = None):
        self.__configure_argument_parser()
        self.__configuration = configuration
        self.__configure_basics(name)

    # --------------------------------------------------------------------------------
    def __configure_basics(self, name: str) -> None:
        self.__application_name     = name
        self.__application_instance = self.command_line_args.instance

        if not self.__configuration:
            if not self.command_line_args.config:
                self.__configuration = load_config_from_environment(self.__application_name, self.__application_instance)
            else:
                self.__configuration = load_config_from_file(self.command_line_args.config)

        if self.__application_instance not in self.__configuration.instances.keys():
            raise InstanceConfigurationNotFoundException(self.__application_name,self.__application_instance)

        self.logger.setup(
            self.__application_name,
            self.__application_instance,
            self.__configuration.instances[self.__application_instance].logging
        )

        self.__statistics_keeper.set_gather_period(
            self.__configuration.instances[self.__application_instance].stats_keeper.gather_period
        )
        self.__statistics_keeper.set_history_length(
            self.__configuration.instances[self.__application_instance].stats_keeper.history_length
        )

        self.__configure_communication_servers()

    # --------------------------------------------------------------------------------
    def __configure_argument_parser(self):
        self.argument_parser.add_argument(
            "-i", "--instance",
            type     = str,
            required = False,
            help     = 'The instance id this invocation of the script needs to run as. Default:"0"',
            default  = "0"
        )

        self.argument_parser.add_argument(
            "-c", "--console",
            type     = bool,
            required = False,
            help     = "Start the application as a console application, rather than a daemon. Default:False",
            default  = False
        )

        self.argument_parser.add_argument(
            "-C", "--config",
            type     = str,
            required = False,
            help     = "Specify a configuration file to load for this invocation. Default:None",
            default  = None
        )

        self.command_line_args = self.argument_parser.parse_args()

    # --------------------------------------------------------------------------------
    def __configure_communication_servers(self):
        if self.__configuration.instances[self.__application_instance].tcp:
            self.__server_tcp = TCPServer(self.__configuration.instances[self.__application_instance].tcp)

        if self.__configuration.instances[self.__application_instance].udp:
            self.__server_udp = UDPServer(self.__configuration.instances[self.__application_instance].udp)

        if self.__configuration.instances[self.__application_instance].uds:
            uds_config = self.__configuration.instances[self.__application_instance].uds
            if uds_config.socket_file_name == "DEFAULT":
                uds_config.socket_file_name = f"{self.__application_name}_{self.__application_instance}_uds.sock"
            self.__server_uds = UDSServer(uds_config)

    # --------------------------------------------------------------------------------
    def __setup_queued_handlers(self):
        queue_directory = self.__configuration.instances[self.__application_instance].queue_directory
        for queued_handler in self.__request_router.get_queued_handlers():
            queued_handler.setup(
                queue_directory,
                self.__application_name,
                self.__application_instance
            )

    # --------------------------------------------------------------------------------
    def start(self):
        self.__setup_queued_handlers()
        self.__running = True
        asyncio.run(self.__start())

    # --------------------------------------------------------------------------------
    def stop(self):
        self.__running = False

    # --------------------------------------------------------------------------------
    def register_handler(self, handler: HandlerBase):
        self.__request_router.register_handler(handler)

    # --------------------------------------------------------------------------------
    async def __start_stats_keeper(self):
        async with self.__statistics_keeper:
            await asyncio.create_task(self.__statistics_keeper.gather_statistics())

    # --------------------------------------------------------------------------------
    async def __start_tcp_server(self):
        if self.__server_tcp:
            async with self.__server_tcp:
                await asyncio.create_task(self.__server_tcp.serve())

    # --------------------------------------------------------------------------------
    async def __start_udp_server(self):
        if self.__server_udp:
            async with self.__server_udp:
                await asyncio.create_task(self.__server_udp.serve())

    # --------------------------------------------------------------------------------
    async def __start_uds_server(self):
        if self.__server_uds:
            async with self.__server_uds:
                await asyncio.create_task(self.__server_uds.serve())

    # --------------------------------------------------------------------------------
    async def __start(self):
        try:
            await asyncio.gather(
                self.__start_stats_keeper(),
                self.__start_tcp_server(),
                self.__start_udp_server(),
                self.__start_uds_server(),
            )
        except asyncio.exceptions.CancelledError:
            self.logger.info(f"Instance [{self.__application_instance}] of application [{self.__application_name}] was stopped.")


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
