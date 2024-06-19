import logging
import uuid

from pydantic import BaseModel as PydanticBaseModel
from abc import ABC, abstractmethod
from typing import Type

from ..state_keepers.statistics_keeper import StatisticsKeeper
from ..state_keepers.error_state_list import ErrorStateList

from ..data_transfer_objects import EmptyDto


# --------------------------------------------------------------------------------
class HandlerBase(ABC):
    def __init__(
        self,
        route_key       : str,
        description     : str,
        request_dto_type: Type[PydanticBaseModel] = EmptyDto
    ):
        self._route_key           : str                     = route_key
        self._description         : str                     = description
        self.request_dto_type     : Type[PydanticBaseModel] = request_dto_type
        self.logger               : logging.Logger          = None
        self.statistics_keeper    : StatisticsKeeper        = None
        self.error_state_list     : ErrorStateList          = None
        self.application_name     : str                     = None
        self.application_instance : str                     = None

    def configure(
        self,
        logger              : logging.Logger,
        statistics_keeper   : StatisticsKeeper,
        error_state_list    : ErrorStateList,
        application_name    : str,
        application_instance: str
    ):
        self.logger               = logger
        self.statistics_keeper    = statistics_keeper
        self.error_state_list     = error_state_list
        self.application_name     = application_name
        self.application_instance = application_instance

    def get_route_key(self) -> str:
        return self._route_key

    def get_description(self) -> str:
        return self._description

    async def attempt_request(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        request_data = self.request_dto_type(**request_data)
        return await self.run(request_uuid, request_data)

    @abstractmethod
    async def run(self, request_uuid: uuid.UUID, request_data) -> PydanticBaseModel:
        pass


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
