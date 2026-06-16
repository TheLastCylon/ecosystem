from pydantic import BaseModel as PydanticBaseModel
from ..data_transfer_objects import SpanKey


# --------------------------------------------------------------------------------
class BufferedMiddlewareBase:
    async def before_push(self, span_key: SpanKey, dto: PydanticBaseModel) -> dict:
        return {}

    async def before_process(self, span_key: SpanKey, dto: PydanticBaseModel, metadata: dict, retries: int) -> None:
        pass

    async def after_process(self, span_key: SpanKey, dto: PydanticBaseModel, metadata: dict, success: bool) -> None:
        pass
