from ekosis.application_base  import ApplicationBase
from ekosis_jaeger_http.setup import initiate_jaeger_tracing

from .endpoints import get_time # noqa

# --------------------------------------------------------------------------------
class CurrentTimeServer(ApplicationBase):
    def __init__(self):
        super().__init__()
        initiate_jaeger_tracing()

# --------------------------------------------------------------------------------
def main():
    with CurrentTimeServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
