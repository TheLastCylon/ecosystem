import os
import asyncio
import signal
import argparse
import logging

from .logs import EcoLogger
from .configuration.config_models import AppConfiguration

from .requests.request_router import RequestRouter

from .servers import (
    TCPServer,
    UDPServer,
    UDSServer,
)

from .state_keepers.queued_sender_keeper import QueuedSenderKeeper
from .state_keepers.error_state_list import ErrorStateList
from .state_keepers.statistics_keeper import StatisticsKeeper

from .util import SingletonType

from .exceptions.exception_base import ExceptionBase

# Pycharm complains that we aren't using these imports,
# but the import is what does the work of getting everything up and
# running. So we do a noqa comment here.
from .standard_endpoints.statistics import eco_statistics_get # noqa
from .standard_endpoints.errors import eco_error_states_get, eco_error_states_clear # noqa
from .standard_endpoints.queued_handler_manager import ( # noqa
    eco_queued_handler_data,
    eco_queued_handler_errors_clear,
    eco_queued_handler_errors_get_first_10,
    eco_queued_handler_errors_inspect_request,
    eco_queued_handler_errors_pop_request,
    eco_queued_handler_errors_reprocess_all,
    eco_queued_handler_errors_reprocess_one,
    eco_queued_handler_processing_pause,
    eco_queued_handler_processing_unpause,
    eco_queued_handler_receiving_pause,
    eco_queued_handler_receiving_unpause,
)
from .standard_endpoints.queued_sender_manager import ( # noqa
    eco_queued_sender_data,
    eco_queued_sender_errors_clear,
    eco_queued_sender_errors_get_first_10,
    eco_queued_sender_errors_inspect_request,
    eco_queued_sender_errors_pop_request,
    eco_queued_sender_errors_reprocess_all,
    eco_queued_sender_errors_reprocess_one,
    eco_queued_sender_send_process_pause,
    eco_queued_sender_send_process_unpause,
)

# --------------------------------------------------------------------------------
class InstanceAlreadyRunningException(ExceptionBase):
    def __init__(
        self,
        application_name: str,
        instance_id     : str,
        process_id      : int
    ):
        super().__init__(f"Instance [{instance_id}] of [{application_name}] already running with process id [{process_id}]!")

# --------------------------------------------------------------------------------
class TerminationSignalException(Exception):
    pass

# --------------------------------------------------------------------------------
class ApplicationBase(metaclass=SingletonType):
    command_line_args     : argparse.Namespace      = None
    logger                : logging.Logger          = logging.getLogger()
    __eco_logger          : EcoLogger               = EcoLogger()
    __request_router      : RequestRouter           = RequestRouter()
    __statistics_keeper   : StatisticsKeeper        = StatisticsKeeper()
    __error_state_list    : ErrorStateList          = ErrorStateList()
    __running             : bool                    = False
    _configuration        : AppConfiguration        = AppConfiguration()
    __server_tcp          : TCPServer               = None
    __server_udp          : UDPServer               = None
    __server_uds          : UDSServer               = None

    # --------------------------------------------------------------------------------
    def __init__(self):
        self.__configure_basics()

    # --------------------------------------------------------------------------------
    @staticmethod
    def __handle_exit_signal(signum, frame):
        raise TerminationSignalException("Exit signal received")

    # --------------------------------------------------------------------------------
    def __setup_signal_handlers(self):
        for x_signal in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(x_signal, self.__handle_exit_signal)

    # --------------------------------------------------------------------------------
    def __enter__(self):
        self.__setup_signal_handlers()
        self.__running = True
        return self

    # --------------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if not isinstance(exc_val, asyncio.CancelledError) \
                    and not isinstance(exc_val, TerminationSignalException):
                import traceback
                self.logger.info(f"Shutdown: EXCEPTION: {exc_type}")
                traceback.print_exception(exc_type, exc_val, exc_tb)
            else:
                self.logger.info(f"Shutdown: Termination signal received.")
        else:
            self.logger.info(f"Shutdown: Application context ending.")

        self.__do_shutdown()
        return True

    # --------------------------------------------------------------------------------
    def __do_shutdown(self):
        self.logger.info("Doing Shutdown.")
        self.__stop_servers()
        self.__shut_down_queued_handlers()
        self.__shut_down_queued_senders()
        self.logger.info(f"Instance [{self._configuration.instance}] of application [{self._configuration.name}] shutdown.")
        self.__eco_logger.flush()

    # --------------------------------------------------------------------------------
    @staticmethod
    def __process_id_check(process_id: int) -> bool:
        try:
            os.kill(process_id, 0)
        except OSError:
            return False
        return True

    # --------------------------------------------------------------------------------
    @staticmethod
    def __create_lock_file(lock_file_path: str):
        process_id = os.getpid()
        with open(lock_file_path, "w") as lock_file:
            lock_file.write(f"{process_id}\n")

    # --------------------------------------------------------------------------------
    def __lock_file_check(self):
        lock_file_name  = f"{self._configuration.name}-{self._configuration.instance}.lock"
        lock_file_path  = f"{self._configuration.lock_directory}/{lock_file_name}"
        if os.path.exists(lock_file_path):
            with open(lock_file_path, "r") as lock_file:
                process_id = int(lock_file.readline())
            if self.__process_id_check(process_id):
                raise InstanceAlreadyRunningException(self._configuration.name, self._configuration.instance, process_id)
            os.remove(lock_file_path)
        self.__create_lock_file(lock_file_path)

    # --------------------------------------------------------------------------------
    def __configure_basics(self) -> None:
        self.__lock_file_check()

        self.__statistics_keeper.set_gather_period(
            self._configuration.stats_keeper.gather_period
        )
        self.__statistics_keeper.set_history_length(
            self._configuration.stats_keeper.history_length
        )

        self.__configure_communication_servers()

    # --------------------------------------------------------------------------------
    def __configure_communication_servers(self):
        if self._configuration.tcp:
            self.__server_tcp = TCPServer(self._configuration.tcp)

        if self._configuration.udp:
            self.__server_udp = UDPServer(self._configuration.udp)

        if self._configuration.uds:
            uds_config = self._configuration.uds
            if uds_config.socket_file_name == "DEFAULT":
                uds_config.socket_file_name = f"{self._configuration.name}_{self._configuration.instance}_uds.sock"
            self.__server_uds = UDSServer(uds_config)

    # --------------------------------------------------------------------------------
    async def __setup_queued_handlers(self):
        queue_directory = self._configuration.queue_directory
        for queued_handler in self.__request_router.get_queued_handlers():
            await queued_handler.setup(
                queue_directory,
                self._configuration.name,
                self._configuration.instance
            )

    # --------------------------------------------------------------------------------
    async def __setup_queued_senders(self):
        queued_sender_keeper = QueuedSenderKeeper()
        queue_directory = self._configuration.queue_directory
        for queued_senders in queued_sender_keeper.get_queued_senders():
            await queued_senders.setup(
                queue_directory,
                self._configuration.name,
                self._configuration.instance
            )

    # --------------------------------------------------------------------------------
    def __shut_down_queued_handlers(self):
        for queued_handler in self.__request_router.get_queued_handlers():
            queued_handler.shut_down()

    # --------------------------------------------------------------------------------
    @staticmethod
    def __shut_down_queued_senders():
        queued_sender_keeper = QueuedSenderKeeper()
        for queued_sender in queued_sender_keeper.get_queued_senders():
            queued_sender.shut_down()

    # --------------------------------------------------------------------------------
    def start(self):
        if not self.__running:
            self.logger.info("Application not running in context. Shutting down.")
            self.__eco_logger.flush()
            return
        asyncio.run(self.__start())

    # --------------------------------------------------------------------------------
    def stop(self):
        self.__running = False

    # --------------------------------------------------------------------------------
    async def __start_stats_keeper(self):
        async with self.__statistics_keeper:
            await self.__statistics_keeper.gather_statistics()

    # --------------------------------------------------------------------------------
    async def __start_tcp_server(self):
        if self.__server_tcp:
            async with self.__server_tcp:
                await self.__server_tcp.serve()

    # --------------------------------------------------------------------------------
    def __stop_tcp_server(self):
        if self.__server_tcp:
            self.__server_tcp.stop()

    # --------------------------------------------------------------------------------
    async def __start_udp_server(self):
        if self.__server_udp:
            async with self.__server_udp:
                await self.__server_udp.serve()

    # --------------------------------------------------------------------------------
    def __stop_udp_server(self):
        if self.__server_udp:
            self.__server_udp.stop()

    # --------------------------------------------------------------------------------
    async def __start_uds_server(self):
        if self.__server_uds:
            async with self.__server_uds:
                await self.__server_uds.serve()

    # --------------------------------------------------------------------------------
    def __stop_uds_server(self):
        if self.__server_uds:
            self.__server_uds.stop()

    # --------------------------------------------------------------------------------
    def __stop_servers(self):
        self.__stop_tcp_server()
        self.__stop_udp_server()
        self.__stop_uds_server()

    # --------------------------------------------------------------------------------
    async def __start(self):
        tasks = []

        await self.__setup_queued_handlers()
        await self.__setup_queued_senders()

        for queued_handler in self.__request_router.get_queued_handlers():
            task = asyncio.create_task(queued_handler.wait_for_shutdown())
            tasks.append(task)

        queued_sender_keeper = QueuedSenderKeeper()
        for queued_sender in queued_sender_keeper.get_queued_senders():
            task = asyncio.create_task(queued_sender.wait_for_shutdown())
            tasks.append(task)

        tasks.append(asyncio.create_task(self.__start_stats_keeper()))
        tasks.append(asyncio.create_task(self.__start_tcp_server()))
        tasks.append(asyncio.create_task(self.__start_udp_server()))
        tasks.append(asyncio.create_task(self.__start_uds_server()))

        self.__eco_logger.flush()
        await asyncio.gather(*tasks)

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
