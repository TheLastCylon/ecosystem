from ekosis.application_base import ApplicationBase

from .database import LogDatabase
from .endpoints import log_request, log_response # noqa

# -------------------------------------------------------------------------------
class TrackerServer(ApplicationBase):
    def __init__(self):
        LogDatabase().initialise()
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with TrackerServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
