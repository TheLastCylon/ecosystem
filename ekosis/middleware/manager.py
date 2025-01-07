from typing import List
from pydantic import BaseModel as PydanticBaseModel
from .middleware_base import MiddlewareBase
from ..util.singleton import SingletonType
from ..data_transfer_objects import RequestDTO

# --------------------------------------------------------------------------------
class MiddlewareManager(metaclass=SingletonType):
    def __init__(self):
        self.middlewares: List[MiddlewareBase] = []

    def add(self, middleware: MiddlewareBase):
        self.middlewares.append(middleware)

    def get_list(self):
        return self.middlewares

    async def run_before_routing(self, **kwargs) -> RequestDTO:
        if len(self.middlewares) < 1:
            return kwargs.get('protocol_dto')
        protocol_dto: RequestDTO = kwargs.get('protocol_dto')
        for middleware in self.middlewares:
            kwargs['protocol_dto'] = protocol_dto
            protocol_dto = await middleware.before_routing(**kwargs)
        return protocol_dto

    async def run_after_routing(self, **kwargs) -> PydanticBaseModel:
        if len(self.middlewares) < 1:
            return kwargs.get('response_dto')
        response_dto: PydanticBaseModel = kwargs.get('response_dto')
        for middleware in self.middlewares:
            kwargs['response_dto'] = response_dto
            response_dto = await middleware.after_routing(**kwargs)
        return response_dto
