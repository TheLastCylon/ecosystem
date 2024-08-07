from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP

from .endpoints import get_joke # noqa


# --------------------------------------------------------------------------------
class DadJokeServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8200)
        self._configuration.stats_keeper.gather_period  = 60
        self._configuration.stats_keeper.history_length = 60
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with DadJokeServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
