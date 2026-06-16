from ekosis.configuration.config_models                          import AppConfiguration
from ekosis.middleware.manager                                   import MiddlewareManager
from ekosis.middleware.buffered_middleware_manager               import BufferedMiddlewareManager
from ekosis_otlp_traces.ekosis_otlp_traces.middleware            import OtlpTracingMiddleware
from ekosis_otlp_traces.ekosis_otlp_traces.buffered_middleware   import OtlpBufferedTracingMiddleware

# --------------------------------------------------------------------------------
def initiate_otlp_tracing():
    config  = AppConfiguration()
    tracer  = OtlpTracingMiddleware(endpoint=config.extra['OTLP_TRACES_ENDPOINT'])
    MiddlewareManager().add(tracer)
    BufferedMiddlewareManager().add(OtlpBufferedTracingMiddleware(tracer))
