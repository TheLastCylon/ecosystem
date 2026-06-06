from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models                        import AppConfiguration
from ekosis.middleware.manager                                 import MiddlewareManager
from ekosis.middleware.buffered_middleware_manager             import BufferedMiddlewareManager
from ekosis_jaeger_http.ekosis_jaeger_http.middleware          import JaegerHttpTracingMiddleware
from ekosis_jaeger_http.ekosis_jaeger_http.buffered_middleware import JaegerHttpBufferedTracingMiddleware

from .endpoints import get_time # noqa

# --------------------------------------------------------------------------------
class CurrentTimeServer(ApplicationBase):
    def __init__(self):
        super().__init__()
        config   = AppConfiguration()
        tracer   = JaegerHttpTracingMiddleware(endpoint = config.extra['JAEGER_ENDPOINT'])
        MiddlewareManager().add(tracer)
        BufferedMiddlewareManager().add(JaegerHttpBufferedTracingMiddleware(tracer))

# --------------------------------------------------------------------------------
def main():
    with CurrentTimeServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
