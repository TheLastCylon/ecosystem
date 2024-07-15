from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP

from .database import LogDatabase
from .endpoints import log_request, log_response # noqa


# -------------------------------------------------------------------------------
class TrackerServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp             = ConfigTCP(host="127.0.0.1", port=8700)
        self._configuration.queue_directory = '/tmp'
        self.log_database                   = LogDatabase()
        self.log_database.initialise(f"/tmp/{self._configuration.name}-{self._configuration.instance}-database.sqlite")
        self._configuration.stats_keeper.gather_period  = 60
        self._configuration.stats_keeper.history_length = 60
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with TrackerServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
