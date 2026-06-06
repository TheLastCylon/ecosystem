import uuid

from typing                        import List
from pydantic                      import BaseModel as PydanticBaseModel
from .buffered_middleware_base     import BufferedMiddlewareBase
from ..util.singleton              import SingletonType


# --------------------------------------------------------------------------------
class BufferedMiddlewareManager(metaclass=SingletonType):
    def __init__(self):
        self.middlewares: List[BufferedMiddlewareBase] = []

    def add(self, middleware: BufferedMiddlewareBase):
        self.middlewares.append(middleware)

    def get_list(self):
        return self.middlewares

    async def collect_push_metadata(self, uid: uuid.UUID, dto: PydanticBaseModel) -> dict:
        metadata = {}
        for middleware in self.middlewares:
            result = await middleware.before_push(uid, dto)
            if result:
                metadata.update(result)
        return metadata

    async def run_before_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, retries: int) -> None:
        for middleware in self.middlewares:
            await middleware.before_process(uid, dto, metadata, retries)

    async def run_after_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, success: bool) -> None:
        for middleware in self.middlewares:
            await middleware.after_process(uid, dto, metadata, success)
