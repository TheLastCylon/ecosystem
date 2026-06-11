import uuid

from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class BufferedMiddlewareBase:
    async def before_push(self, uid: uuid.UUID, dto: PydanticBaseModel) -> dict:
        return {}

    async def before_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, retries: int) -> None:
        pass

    async def after_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, success: bool) -> None:
        pass
