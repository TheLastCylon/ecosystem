from ekosis.application_base import ApplicationBase
from ekosis_jaeger_http.setup import initiate_jaeger_tracing

from .database import LogDatabase
from .endpoints import log_request, log_response # noqa

# -------------------------------------------------------------------------------
class TrackerServer(ApplicationBase):
    def __init__(self):
        LogDatabase().initialise()
        super().__init__()
        initiate_jaeger_tracing()

# --------------------------------------------------------------------------------
def main():
    with TrackerServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
