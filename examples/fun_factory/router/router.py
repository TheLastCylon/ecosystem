from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP

from .endpoints import process_message # noqa


# --------------------------------------------------------------------------------
class RouterServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp             = ConfigTCP(host="127.0.0.1", port=8600)
        self._configuration.queue_directory = '/tmp'
        self._configuration.stats_keeper.gather_period  = 60
        self._configuration.stats_keeper.history_length = 60
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with RouterServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
