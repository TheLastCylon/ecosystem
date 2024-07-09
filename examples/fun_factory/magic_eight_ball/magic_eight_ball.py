from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP

from .endpoints import get_prediction # noqa


# --------------------------------------------------------------------------------
class Magic8Ball(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=4444)
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with Magic8Ball() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
