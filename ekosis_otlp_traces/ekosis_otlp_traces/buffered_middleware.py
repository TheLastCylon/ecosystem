from opentelemetry       import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
from pydantic            import BaseModel as PydanticBaseModel

from ekosis.middleware.buffered_middleware_base import BufferedMiddlewareBase
from ekosis.data_transfer_objects              import SpanKey

from .middleware import OtlpTracingMiddleware

_RECEIVE_SPAN_ID_KEY = "otlp_receive_span_id"

# --------------------------------------------------------------------------------
class OtlpBufferedTracingMiddleware(BufferedMiddlewareBase):
    def __init__(self, tracing_middleware: OtlpTracingMiddleware):
        self._tracing       = tracing_middleware
        self._process_spans = {}

    # --------------------------------------------------------------------------------
    async def before_push(self, span_key: SpanKey, dto: PydanticBaseModel) -> dict:
        span = self._tracing.get_active_span(span_key)
        if not span:
            return {}
        return {_RECEIVE_SPAN_ID_KEY: span.get_span_context().span_id}

    # --------------------------------------------------------------------------------
    async def before_process(self, span_key: SpanKey, dto: PydanticBaseModel, metadata: dict, retries: int) -> None:
        receive_span_id = metadata.get(_RECEIVE_SPAN_ID_KEY)
        parent_span_id  = receive_span_id if receive_span_id is not None else span_key.span_id.value
        is_remote       = receive_span_id is None
        parent_context  = trace.set_span_in_context(NonRecordingSpan(SpanContext(
            trace_id    = span_key.trace_id.int,
            span_id     = parent_span_id,
            is_remote   = is_remote,
            trace_flags = TraceFlags(TraceFlags.SAMPLED),
        )))
        span = self._tracing._tracer.start_span(
            f"{dto.__class__.__name__}.process",
            context = parent_context,
        )
        span.set_attribute("request.trace_id", str(span_key.trace_id))
        span.set_attribute("request.span_id",  str(span_key.span_id))
        span.set_attribute("request.retries",  retries)
        self._process_spans[span_key] = span

    # --------------------------------------------------------------------------------
    async def after_process(self, span_key: SpanKey, dto: PydanticBaseModel, metadata: dict, success: bool) -> None:
        span = self._process_spans.pop(span_key, None)
        if span:
            span.set_attribute("process.success", success)
            span.end()
