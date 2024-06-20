import asyncio
import logging
import argparse

from typing import List

from .logs import setup_logger

from .requests import HandlerBase
from .requests import RequestRouter

from .servers import TCPServer
from .servers import UDPServer
from .servers import UDSServer

from .standard_handlers import ErrorCleaner
from .standard_handlers import ErrorReporter
from .standard_handlers import Statistics

from .state_keepers import ErrorStateList
from .state_keepers import StatisticsKeeper

from .configuration import ConfigApplication
from .configuration import load_config_from_file
from .configuration import load_config_from_environment

from .util import SingletonType


# --------------------------------------------------------------------------------
class ApplicationBase(metaclass=SingletonType):
    argument_parser       : argparse.ArgumentParser = argparse.ArgumentParser()
    command_line_args     : argparse.Namespace      = None
    logger                : logging.Logger          = None
    __configuration       : ConfigApplication       = None
    __application_name    : str                     = None
    __application_instance: str                     = None
    __running             : bool                    = False
    __statistics_keeper   : StatisticsKeeper        = None
    __request_router      : RequestRouter           = None
    __error_state_list    : ErrorStateList          = None
    __handlers            : List[HandlerBase]       = None
    __server_tcp          : TCPServer               = None
    __server_udp          : UDPServer               = None
    __server_uds          : UDSServer               = None

    def __init__(
        self,
        name         : str,
        handlers     : List[HandlerBase],
        configuration: ConfigApplication = None,
    ):
        self.__configure_argument_parser()
        self.__configuration = configuration
        self.__configure_basics(name, handlers)
        self.__configure_communication_servers()

    # --------------------------------------------------------------------------------
    def __configure_basics(
        self,
        name         : str,
        handlers     : List[HandlerBase],
    ) -> None:
        self.__application_name     = name
        self.__application_instance = self.command_line_args.instance

        if not self.__configuration:
            if not self.command_line_args.config:
                self.__configuration = load_config_from_environment(self.__application_name, self.__application_instance)
            else:
                self.__configuration = load_config_from_file(self.command_line_args.config)

        self.logger = setup_logger(
            self.__application_name,
            self.__application_instance,
            self.__configuration.instances[self.__application_instance].logging
        )

        self.__statistics_keeper = StatisticsKeeper(
            self.logger,
            self.__configuration.instances[self.__application_instance].stats_keeper.gather_period,
            self.__configuration.instances[self.__application_instance].stats_keeper.history_length
        )

        self.__request_router   = RequestRouter(self.__statistics_keeper, self.logger)
        self.__error_state_list = ErrorStateList()
        self.__handlers         = handlers

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
            self.__server_tcp = TCPServer(
                self.__configuration.instances[self.__application_instance].tcp,
                self.logger,
                self.__request_router
            )

        if self.__configuration.instances[self.__application_instance].udp:
            self.__server_udp = UDPServer(
                self.__configuration.instances[self.__application_instance].udp,
                self.logger,
                self.__request_router
            )

        if self.__configuration.instances[self.__application_instance].uds:
            uds_config = self.__configuration.instances[self.__application_instance].uds
            if uds_config.socket_file_name == "DEFAULT":
                uds_config.socket_file_name = f"{self.__application_name}_{self.__application_instance}_uds.sock"

            self.__server_uds = UDSServer(
                uds_config,
                self.logger,
                self.__request_router
            )

    # --------------------------------------------------------------------------------
    def start(self):
        self.__register_handlers()
        self.__running = True
        self.__statistics_keeper.set_logger(self.logger)
        asyncio.run(self.__start())

    # --------------------------------------------------------------------------------
    def stop(self):
        self.__running = False

    # --------------------------------------------------------------------------------
    def register_handler(self, handler: HandlerBase):
        handler.configure(
            self.logger,
            self.__statistics_keeper,
            self.__error_state_list,
            self.__application_name,
            self.__application_instance
        )
        self.__request_router.register_handler(handler)

    # --------------------------------------------------------------------------------
    def __register_handlers(self):
        self.__register_standard_handlers()
        for handler in self.__handlers:
            self.register_handler(handler)

    # --------------------------------------------------------------------------------
    def __register_standard_handlers(self):
        self.register_handler(Statistics())
        self.register_handler(ErrorReporter())
        self.register_handler(ErrorCleaner())

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
