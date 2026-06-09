from ekosis.configuration.config_models                        import AppConfiguration
from ekosis.middleware.manager                                 import MiddlewareManager
from ekosis.middleware.buffered_middleware_manager             import BufferedMiddlewareManager
from ekosis_jaeger_http.ekosis_jaeger_http.middleware          import JaegerHttpTracingMiddleware
from ekosis_jaeger_http.ekosis_jaeger_http.buffered_middleware import JaegerHttpBufferedTracingMiddleware

def initiate_jaeger_tracing():
    config   = AppConfiguration()
    tracer   = JaegerHttpTracingMiddleware(endpoint = config.extra['JAEGER_ENDPOINT'])
    MiddlewareManager().add(tracer)
    BufferedMiddlewareManager().add(JaegerHttpBufferedTracingMiddleware(tracer))
