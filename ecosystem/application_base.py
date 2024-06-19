import asyncio
import logging

from typing import List

from .logging import setup_logger

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

from .util import SingletonType


# --------------------------------------------------------------------------------
class ApplicationBase(metaclass=SingletonType):
    def __init__(
        self,
        name         : str,
        instance     : str,
        host         : str,
        tcp_port     : int,
        udp_port     : int,
        handlers     : List[HandlerBase],
        log_directory: str = '/tmp',
    ):
        self.logger                : logging.Logger    = setup_logger(log_directory, name, instance)
        self.__running             : bool              = False
        self.__application_name    : str               = name
        self.__application_instance: str               = instance
        self.__statistics_keeper   : StatisticsKeeper  = StatisticsKeeper(self.logger)
        self.__request_router      : RequestRouter     = RequestRouter(self.__statistics_keeper, self.logger)
        self.__error_state_list    : ErrorStateList    = ErrorStateList()
        self.__handlers            : List[HandlerBase] = handlers

        self.__server_tcp: TCPServer = TCPServer(host, tcp_port, self.logger, self.__request_router)
        self.__server_udp: UDPServer = UDPServer(host, udp_port, self.logger, self.__request_router)
        self.__server_uds: UDSServer = UDSServer(
            f"/tmp/{name}_{instance}_uds.sock",
            self.logger,
            self.__request_router,
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
        async with self.__server_tcp:
            await asyncio.create_task(self.__server_tcp.serve())

    # --------------------------------------------------------------------------------
    async def __start_udp_server(self):
        async with self.__server_udp:
            await asyncio.create_task(self.__server_udp.serve())

    # --------------------------------------------------------------------------------
    async def __start_uds_server(self):
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
