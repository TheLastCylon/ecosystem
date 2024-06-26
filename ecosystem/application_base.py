import os
import asyncio
import signal
import argparse

from .logs import EcoLogger

from .requests.request_router import RequestRouter

from .servers import TCPServer
from .servers import UDPServer
from .servers import UDSServer

from .state_keepers import ErrorStateList
from .state_keepers import StatisticsKeeper

from .configuration import ConfigApplication
from .configuration import load_config_from_file
from .configuration import load_config_from_environment

from .util import SingletonType

from .exceptions import (
    InstanceConfigurationNotFoundException,
    InstanceAlreadyRunningException,
    TerminationSignalException
)

# Pycharm complains that we aren't using these imports,
# but the import is what does the work of getting everything up and
# running. So we do a noqa on each.
from .standard_endpoints import standard_endpoint_error_clear  # noqa
from .standard_endpoints import standard_endpoint_statistics   # noqa
from .standard_endpoints import queue_receiving_pause          # noqa
from .standard_endpoints import queue_receiving_unpause        # noqa
from .standard_endpoints import queue_processing_pause         # noqa
from .standard_endpoints import queue_processing_unpause       # noqa
from .standard_endpoints import error_queue_pop_request        # noqa
from .standard_endpoints import error_queue_inspect_request    # noqa
from .standard_endpoints import error_queue_reprocess_all      # noqa
from .standard_endpoints import error_queue_reprocess_request  # noqa


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
        # TODO: Shut down queued senders
        self.logger.info(f"Instance [{self.__application_instance}] of application [{self.__application_name}] shutdown.")

    # --------------------------------------------------------------------------------
    def __init__(self, name: str, configuration: ConfigApplication = None):
        self.__configure_argument_parser()
        self.__configuration = configuration
        self.__configure_basics(name)

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
        instance_config = self.__configuration.instances[self.__application_instance]
        lock_file_name  = f"{self.__application_name}-{self.__application_instance}.lock"
        lock_file_path  = f"{instance_config.lock_directory}/{lock_file_name}"
        if os.path.exists(lock_file_path):
            with open(lock_file_path, "r") as lock_file:
                process_id = int(lock_file.readline())
            if self.__process_id_check(process_id):
                raise InstanceAlreadyRunningException(self.__application_name, self.__application_instance, process_id)
            os.remove(lock_file_path)
        self.__create_lock_file(lock_file_path)

    # --------------------------------------------------------------------------------
    def __load_configuration(self):
        if not self.__configuration:
            if not self.command_line_args.config:
                self.__configuration = load_config_from_environment(self.__application_name, self.__application_instance)
            else:
                self.__configuration = load_config_from_file(self.command_line_args.config)

        if self.__application_instance not in self.__configuration.instances.keys():
            raise InstanceConfigurationNotFoundException(self.__application_name, self.__application_instance)

    # --------------------------------------------------------------------------------
    def __configure_basics(self, name: str) -> None:
        self.__application_name     = name
        self.__application_instance = self.command_line_args.instance

        self.__load_configuration()
        self.__lock_file_check()

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
    async def __setup_queued_handlers(self):
        queue_directory = self.__configuration.instances[self.__application_instance].queue_directory
        for queued_handler in self.__request_router.get_queued_handlers():
            await queued_handler.setup(
                queue_directory,
                self.__application_name,
                self.__application_instance
            )

    # --------------------------------------------------------------------------------
    def __shut_down_queued_handlers(self):
        for queued_handler in self.__request_router.get_queued_handlers():
            queued_handler.shut_down()

    # --------------------------------------------------------------------------------
    def start(self):
        if not self.__running:
            self.logger.info("Application not running in context. Shutting down.")
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
        for queued_handler in self.__request_router.get_queued_handlers():
            task = asyncio.create_task(queued_handler.wait_for_shutdown())
            tasks.append(task)

        tasks.append(asyncio.create_task(self.__start_stats_keeper()))
        tasks.append(asyncio.create_task(self.__start_tcp_server()))
        tasks.append(asyncio.create_task(self.__start_udp_server()))
        tasks.append(asyncio.create_task(self.__start_uds_server()))

        await asyncio.gather(*tasks)


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
