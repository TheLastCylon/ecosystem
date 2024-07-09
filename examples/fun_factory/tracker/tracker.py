from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP

from .database import LogDatabase
from .endpoints import log_request, log_response # noqa


# -------------------------------------------------------------------------------
class TrackerServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp             = ConfigTCP(host="127.0.0.1", port=7777)
        self._configuration.queue_directory = '/tmp'
        self.log_database                   = LogDatabase()
        self.log_database.initialise(f"/tmp/{self._configuration.name}-{self._configuration.instance}-database.sqlite")
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with TrackerServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
