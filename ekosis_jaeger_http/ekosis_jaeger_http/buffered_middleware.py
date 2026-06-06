import uuid

from opentelemetry                             import trace
from opentelemetry.trace                       import NonRecordingSpan, SpanContext, TraceFlags
from pydantic                                  import BaseModel as PydanticBaseModel
from ekosis.middleware.buffered_middleware_base import BufferedMiddlewareBase
from .middleware                               import JaegerHttpTracingMiddleware

_TRACE_ID_KEY = "jaeger_trace_id"
_SPAN_ID_KEY  = "jaeger_span_id"


# --------------------------------------------------------------------------------
class JaegerHttpBufferedTracingMiddleware(BufferedMiddlewareBase):
    def __init__(self, tracing_middleware: JaegerHttpTracingMiddleware):
        self._tracing        = tracing_middleware
        self._process_spans  = {}

    async def before_push(self, uid: uuid.UUID, dto: PydanticBaseModel) -> dict:
        span = self._tracing.get_active_span(str(uid))
        if not span:
            return {}
        ctx = span.get_span_context()
        return {
            _TRACE_ID_KEY: ctx.trace_id,
            _SPAN_ID_KEY : ctx.span_id,
        }

    async def before_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, retries: int) -> None:
        trace_id = metadata.get(_TRACE_ID_KEY)
        span_id  = metadata.get(_SPAN_ID_KEY)
        if trace_id is None or span_id is None:
            return
        parent_context = trace.set_span_in_context(
            NonRecordingSpan(SpanContext(
                trace_id    = trace_id,
                span_id     = span_id,
                is_remote   = True,
                trace_flags = TraceFlags(TraceFlags.SAMPLED),
            ))
        )
        span = self._tracing._tracer.start_span(
            f"{dto.__class__.__name__}.process",
            context = parent_context,
        )
        span.set_attribute("request.uid",     str(uid))
        span.set_attribute("request.retries", retries)
        self._process_spans[str(uid)] = span

    async def after_process(self, uid: uuid.UUID, dto: PydanticBaseModel, metadata: dict, success: bool) -> None:
        span = self._process_spans.pop(str(uid), None)
        if span:
            span.set_attribute("process.success", success)
            span.end()
