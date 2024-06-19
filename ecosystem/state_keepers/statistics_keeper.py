import logging
import asyncio
import time

from typing import Any, Dict, List

from ..util import SingletonType
from ..queues import SqlPersistedQueue


# --------------------------------------------------------------------------------
class StatisticsKeeper(metaclass=SingletonType):
    def __init__(self, logger: logging.Logger = None, gather_period: int = 300, history_length: int = 12):
        self.__running           : bool                         = False
        self.__logger            : logging.Logger               = logger
        self.__gather_period     : int                          = gather_period
        self.__history_length    : int                          = history_length
        self.__start_time        : int                          = int(time.time())
        self.__statistics_current: Dict[str, Any]               = {}
        self.__statistics_history: Dict[str, List[float]]       = {}
        self.__persisted_queues  : Dict[str, SqlPersistedQueue] = {}

    def set_logger(self, logger: logging.Logger):
        self.__logger = logger

    async def get_current_statistics(self) -> Dict[str, Any]:
        for key in self.__persisted_queues.keys():
            self.__statistics_current[key] = await self.__persisted_queues[key].size()
        self.__statistics_current['uptime'] = int(time.time())-self.__start_time
        return self.__statistics_current

    async def get_last_gathered_statistics(self) -> Dict[str, float]:
        last_gathered_statistics: Dict[str, float] = {}
        for key in self.__statistics_history.keys():
            last_gathered_statistics[key] = self.__statistics_history[key][0]
        return last_gathered_statistics

    async def get_full_gathered_statistics(self) -> Dict[str, List[float]]:
        return self.__statistics_history

    async def set_statistic_value(self, key: str, value: float):
        self.__statistics_current[key] = value

    @staticmethod
    def __deep_get(dictionary, keys):
        for key in keys:
            if isinstance(dictionary, dict):
                dictionary = dictionary.get(key, None)
            else:
                return None
        return dictionary

    @staticmethod
    def __deep_set(dictionary, keys, value):
        for key in keys[:-1]:
            dictionary = dictionary.setdefault(key, {})
        dictionary[keys[-1]] = value

    def __get_statistic_value(self, dictionary, keys) -> float:
        value = self.__deep_get(dictionary, keys)
        if value is None:
            return 0
        else:
            return value

    def increment(self, key: str, value: float = 1):
        keys          = key.split('.')
        current_value = self.__get_statistic_value(self.__statistics_current, keys)
        self.__deep_set(self.__statistics_current, keys, current_value+value)

    def decrement(self, key: str, value: float = 1):
        keys          = key.split('.')
        current_value = self.__get_statistic_value(self.__statistics_current, keys)
        self.__deep_set(self.__statistics_current, keys, current_value-value)

    def add_persisted_queue(self, key: str, queue: SqlPersistedQueue):
        self.__persisted_queues[key] = queue

    async def __aenter__(self):
        self.__start_time = int(time.time())
        self.__running    = True
        self.__logger.info("Starting stats gathering.")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__running = False
        self.__logger.info("Stopping stats gathering.")

    async def gather_statistics(self):
        while self.__running:
            sleep_count: int = 0

            while self.__running and sleep_count < self.__gather_period:
                await asyncio.sleep(1)
                sleep_count += 1

            if self.__running:
                self.__logger.info(f"Gathering statistics")
                self.__statistics_current['uptime'] = int(time.time())-self.__start_time

                for key in self.__persisted_queues.keys():
                    if key not in self.__statistics_history.keys():
                        self.__statistics_history[key] = []
                    self.__statistics_history[key].insert(0, await self.__persisted_queues[key].size())

                for key in self.__statistics_current.keys():
                    if key not in self.__statistics_history.keys():
                        self.__statistics_history[key] = []

                    self.__statistics_history[key].insert(0, self.__statistics_current[key])
                    if len(self.__statistics_history[key]) > self.__history_length:
                        self.__statistics_history[key].pop()
