import logging
from pydantic import BaseModel as PydanticBaseModel
from ekosis.middleware.middleware_base import MiddlewareBase
from ekosis.data_transfer_objects import RequestDTO

log = logging.getLogger()

# --------------------------------------------------------------------------------
class MiddlewareTest(MiddlewareBase):
    async def before_routing(self, protocol_dto: RequestDTO, **kwargs) -> RequestDTO:
        if protocol_dto.route_key != "app.a.middleware_test":
            return protocol_dto
        protocol_dto.data["before_routing"] = True
        return protocol_dto

    async def after_routing(self, protocol_dto: RequestDTO, response_dto: PydanticBaseModel, **kwargs) -> PydanticBaseModel:
        if protocol_dto.route_key != "app.a.middleware_test":
            return response_dto
        response_dto.before_routing = protocol_dto.data["before_routing"]
        response_dto.after_routing  = True
        return response_dto
