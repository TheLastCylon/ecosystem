from ekosis.application_base import ApplicationBase
from ekosis_otlp_traces.setup import initiate_otlp_tracing

from .database import LogDatabase
from .endpoints import log_request, log_response # noqa

# -------------------------------------------------------------------------------
class TrackerServer(ApplicationBase):
    def __init__(self):
        LogDatabase().initialise()
        super().__init__()
        initiate_otlp_tracing()

# --------------------------------------------------------------------------------
def main():
    with TrackerServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
