import asyncio
import time
import copy
import logging

from typing import Any, Dict, List

from ..util import SingletonType
from ..queues import SqlPersistedQueue


# --------------------------------------------------------------------------------
class StatisticsKeeper(metaclass=SingletonType):
    __running           : bool                         = False
    __logger            : logging.Logger               = logging.getLogger()
    __gather_period     : int                          = 300
    __history_length    : int                          = 12
    __start_time        : int                          = int(time.time())
    __statistics_current: Dict[str, Any]               = {}
    __statistics_history: List[Dict[str, Any]]         = []
    __persisted_queues  : Dict[str, SqlPersistedQueue] = {}

    def __init__(self):
        pass

    def set_gather_period(self, gather_period: int):
        self.__gather_period = gather_period

    def set_history_length(self, history_length: int):
        self.__history_length = history_length

    async def __update_current_statistics(self):
        current_time = time.time()
        self.__statistics_current['timestamp'] = int(current_time)
        self.__statistics_current['uptime']    = int(current_time)-self.__start_time
        for key in self.__persisted_queues.keys():
            await self.set_statistic_value(key, await self.__persisted_queues[key].size())

    async def get_current_statistics(self) -> Dict[str, Any]:
        await self.__update_current_statistics()
        return self.__statistics_current

    async def get_last_gathered_statistics(self) -> Dict[str, Any]:
        if len(self.__statistics_history) > 0:
            return self.__statistics_history[0]
        else:
            return {}

    async def get_full_gathered_statistics(self) -> List[Dict[str, Any]]:
        return self.__statistics_history

    async def set_statistic_value(self, key: str, value: float):
        keys = key.split('.')
        self.__deep_set(self.__statistics_current, keys, value)

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

    def __reset_stats(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__reset_stats(value)
            else:
                dictionary[key] = 0

    async def __reset_current_statistics(self):
        self.__reset_stats(self.__statistics_current)

    async def gather_statistics(self):
        while self.__running:
            sleep_count: int = 0

            while self.__running and sleep_count < self.__gather_period:
                await asyncio.sleep(1)
                sleep_count += 1

            if self.__running:
                self.__logger.info(f"Gathering statistics")
                await self.__update_current_statistics()
                self.__statistics_history.insert(0, copy.deepcopy(self.__statistics_current))
                if len(self.__statistics_history) > self.__history_length:
                    self.__statistics_history.pop()
                await self.__reset_current_statistics()
