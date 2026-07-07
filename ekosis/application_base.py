import os
import fcntl
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

from .state_keepers.buffered_sender_keeper import BufferedSenderKeeper
from .state_keepers.error_state_list import ErrorStateList
from .state_keepers.statistics_keeper import StatisticsKeeper

from .util import SingletonType

from .exceptions.exception_base import ExceptionBase

# Pycharm complains that we aren't using these imports,
# but the import is what does the work of getting everything up and
# running. So we do a noqa comment here.
from .standard_endpoints.log_manager import eco_log_level, eco_log_buffer # noqa
from .standard_endpoints.statistics import eco_statistics_get # noqa
from .standard_endpoints.errors import eco_error_states_get, eco_error_states_clear # noqa
from .standard_endpoints.buffered_handler_manager import ( # noqa
    eco_buffered_handler_data,
    eco_buffered_handler_errors_clear,
    eco_buffered_handler_errors_get_first_10,
    eco_buffered_handler_errors_inspect_request,
    eco_buffered_handler_errors_pop_request,
    eco_buffered_handler_errors_reprocess_all,
    eco_buffered_handler_errors_reprocess_one,
    eco_buffered_handler_processing_pause,
    eco_buffered_handler_processing_unpause,
    eco_buffered_handler_receiving_pause,
    eco_buffered_handler_receiving_unpause,
)
from .standard_endpoints.buffered_sender_manager import ( # noqa
    eco_buffered_sender_data,
    eco_buffered_sender_errors_clear,
    eco_buffered_sender_errors_get_first_10,
    eco_buffered_sender_errors_inspect_request,
    eco_buffered_sender_errors_pop_request,
    eco_buffered_sender_errors_reprocess_all,
    eco_buffered_sender_errors_reprocess_one,
    eco_buffered_sender_send_process_pause,
    eco_buffered_sender_send_process_unpause,
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
    __lock_fd             : int                     = None
    __lock_file_path      : str                     = None

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
        self.__shut_down_buffered_handlers()
        self.__shut_down_buffered_senders()
        self.__release_lock_file()
        self.logger.info(f"Instance [{self._configuration.instance}] of application [{self._configuration.name}] shutdown.")
        self.__eco_logger.flush()

    # --------------------------------------------------------------------------------
    # Closing the fd releases the flock() automatically, but doing it explicitly
    # here (rather than just letting process exit handle it) keeps the unlink
    # ordered after the unlock, and makes both steps visible in one place.
    def __release_lock_file(self):
        if self.__lock_fd is not None:
            fcntl.flock(self.__lock_fd, fcntl.LOCK_UN)
            os.close(self.__lock_fd)
            os.remove(self.__lock_file_path)
            self.__lock_fd = None

    # --------------------------------------------------------------------------------
    # A previous PID-read-then-kill(pid, 0) check here had two bugs:
    # 1. A TOCTOU (time-of-check-time-of-use) race condition:
    #    Two processes starting concurrently could both read the file, both see the PID
    #    as dead, and both proceed to remove/recreate the lock;
    # 2. kill(pid, 0) raising OSError doesn't distinguish ESRCH (process-gone, lock stale)
    #    from EPERM (process-alive, just owned by another user):
    #    Both were being treated as "stale, delete it," so a live process owned by another
    #    user would get its lock silently stolen.
    # flock() fixes both issues: it's atomic at  the kernel level (no race window), and
    #    it doesn't care who owns the other process, only whether a lock is actually held.
    def __lock_file_check(self):
        lock_file_name = f"{self._configuration.name}-{self._configuration.instance}.lock"
        lock_file_path = f"{self._configuration.lock_directory}/{lock_file_name}"

        # O_CREAT here does NOT race with another instance doing the same flock(), below is
        # the actual exclusion mechanism, atomic at the kernel level. Two processes can both
        # open() the same path successfully; only one can hold LOCK_EX at a time.
        fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR, 0o644)

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            # Another live process holds the lock. Read whatever PID it last wrote purely for
            # the error message, the lock itself, not this PID read, is what proved it's alive.
            try:
                process_id = int(os.read(fd, 64).decode().strip() or 0)
            except ValueError:
                process_id = 0
            os.close(fd)
            raise InstanceAlreadyRunningException(self._configuration.name, self._configuration.instance, process_id)

        # We hold the lock. A previous run's stale PID (if the file already existed from a crash) is irrelevant.
        # flock() above already proved no live holder exists. Truncate and overwrite with our own PID.
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())

        self.__lock_fd        = fd # kept open for the process lifetime. Closing it releases the flock
        self.__lock_file_path = lock_file_path

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
                uds_config.socket_file_name = f"{self._configuration.name}_{self._configuration.instance}.uds.sock"
            self.__server_uds = UDSServer(uds_config)

    # --------------------------------------------------------------------------------
    async def __setup_buffered_handlers(self):
        buffer_directory = self._configuration.buffer_directory
        for buffered_handler in self.__request_router.get_buffered_handlers():
            await buffered_handler.setup(
                buffer_directory,
                self._configuration.name,
                self._configuration.instance
            )

    # --------------------------------------------------------------------------------
    async def __setup_buffered_senders(self):
        buffered_sender_keeper = BufferedSenderKeeper()
        buffer_directory = self._configuration.buffer_directory
        for buffered_senders in buffered_sender_keeper.get_buffered_senders():
            await buffered_senders.setup(
                buffer_directory,
                self._configuration.name,
                self._configuration.instance
            )

    # --------------------------------------------------------------------------------
    def __shut_down_buffered_handlers(self):
        for buffered_handler in self.__request_router.get_buffered_handlers():
            buffered_handler.shut_down()

    # --------------------------------------------------------------------------------
    @staticmethod
    def __shut_down_buffered_senders():
        buffered_sender_keeper = BufferedSenderKeeper()
        for buffered_sender in buffered_sender_keeper.get_buffered_senders():
            buffered_sender.shut_down()

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
    async def setup_tasks(self, tasks: list):
        pass

    # --------------------------------------------------------------------------------
    async def __start(self):
        tasks = []

        await self.__setup_buffered_handlers()
        await self.__setup_buffered_senders()

        for buffered_handler in self.__request_router.get_buffered_handlers():
            task = asyncio.create_task(buffered_handler.wait_for_shutdown())
            tasks.append(task)

        buffered_sender_keeper = BufferedSenderKeeper()
        for buffered_sender in buffered_sender_keeper.get_buffered_senders():
            task = asyncio.create_task(buffered_sender.wait_for_shutdown())
            tasks.append(task)

        tasks.append(asyncio.create_task(self.__start_stats_keeper()))
        tasks.append(asyncio.create_task(self.__start_tcp_server()))
        tasks.append(asyncio.create_task(self.__start_udp_server()))
        tasks.append(asyncio.create_task(self.__start_uds_server()))

        await self.setup_tasks(tasks)

        self.__eco_logger.flush()
        await asyncio.gather(*tasks)
