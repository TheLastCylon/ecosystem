from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP

from .endpoints import get_joke # noqa


# --------------------------------------------------------------------------------
class DadJokeServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=2222)
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with DadJokeServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
