import uuid

from typing import Any
from pydantic import BaseModel as PydanticBaseModel
from .span_id import SpanId, span_id_gen

# --------------------------------------------------------------------------------
class SpanKey(PydanticBaseModel):
    trace_id : uuid.UUID
    span_id  : SpanId

    @classmethod
    def generate(cls) -> 'SpanKey':
        return cls(trace_id=uuid.uuid4(), span_id=span_id_gen())

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SpanKey':
        return cls(
            trace_id = uuid.UUID(bytes=data[:16]),
            span_id  = SpanId(bytes_=data[16:])
        )

    @classmethod
    def from_hex(cls, data: str) -> 'SpanKey':
        trace_id_end = data.find(':')
        trace_id_hex = data[:trace_id_end]
        span_id_hex  = data[trace_id_end+1:]
        return cls(
            trace_id = uuid.UUID(hex = trace_id_hex),
            span_id  = SpanId(hex_ = span_id_hex)
        )

    @property
    def bytes(self) -> bytes:
        return self.trace_id.bytes + self.span_id.bytes

    def key(self):
        return self.bytes

    def __eq__(self, other: 'SpanKey') -> bool:
        if isinstance(other, SpanKey):
            return self.bytes == other.bytes
        if isinstance(other, str):
            return self.bytes == SpanKey.from_hex(other).bytes
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.bytes)

    def __repr__(self) -> str:
        return f"SpanKey({self.trace_id}:{self.span_id})"

    def __str__(self) -> str:
        return f"{self.trace_id}:{self.span_id}"

# --------------------------------------------------------------------------------
class RequestDTO(PydanticBaseModel):
    route_key: str
    span_key : SpanKey
    data     : Any

# --------------------------------------------------------------------------------
class ResponseDTO(PydanticBaseModel):
    span_key: SpanKey | None = None
    status  : int
    data    : Any
