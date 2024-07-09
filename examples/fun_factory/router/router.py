from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP

from .endpoints import process_message # noqa


# --------------------------------------------------------------------------------
class RouterServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp             = ConfigTCP(host="127.0.0.1", port=6666)
        self._configuration.queue_directory = '/tmp'
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with RouterServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
