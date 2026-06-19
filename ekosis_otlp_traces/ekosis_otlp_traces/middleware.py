from opentelemetry                             import trace
from opentelemetry.sdk.trace                   import TracerProvider
from opentelemetry.sdk.trace.export            import BatchSpanProcessor
from opentelemetry.sdk.resources               import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.semconv.attributes.service_attributes   import SERVICE_NAME
from opentelemetry.trace                       import StatusCode, NonRecordingSpan, SpanContext, TraceFlags
from pydantic                                  import BaseModel as PydanticBaseModel
from ekosis.middleware.middleware_base         import MiddlewareBase
from ekosis.data_transfer_objects              import RequestDTO, SpanKey
from ekosis.configuration.config_models        import AppConfiguration

# --------------------------------------------------------------------------------
class OtlpTracingMiddleware(MiddlewareBase):
    _active_spans        = {}
    application_name     = AppConfiguration().name
    application_instance = AppConfiguration().instance

    def __init__(
        self,
        endpoint    : str = "http://localhost:4318/v1/traces",
        service_name: str = f"{application_name}-{application_instance}",
    ):
        resource = Resource.create({SERVICE_NAME: service_name})
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(service_name)

    # --------------------------------------------------------------------------------
    async def before_routing(self, protocol_dto: RequestDTO, **kwargs) -> RequestDTO:
        span_key   = protocol_dto.span_key
        parent_ctx = trace.set_span_in_context(NonRecordingSpan(SpanContext(
            trace_id    = span_key.trace_id.int,
            span_id     = span_key.span_id.value,
            is_remote   = True,
            trace_flags = TraceFlags(TraceFlags.SAMPLED),
        )))
        span = self._tracer.start_span(protocol_dto.route_key, context=parent_ctx)
        span.set_attribute("request.trace_id",  str(span_key.trace_id))
        span.set_attribute("request.span_id",   str(span_key.span_id))
        span.set_attribute("request.route_key", protocol_dto.route_key)
        self._active_spans[span_key] = span
        return protocol_dto

    # --------------------------------------------------------------------------------
    async def after_routing(self, protocol_dto: RequestDTO, response_dto: PydanticBaseModel, **kwargs) -> PydanticBaseModel:
        span = self._active_spans.pop(protocol_dto.span_key, None)
        if span:
            span.set_status(StatusCode.OK)
            span.end()
        return response_dto

    # --------------------------------------------------------------------------------
    def get_active_span(self, span_key: SpanKey):
        return self._active_spans.get(span_key)
