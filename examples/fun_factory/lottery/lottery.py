from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP

from .endpoints import pick_numbers_endpoint # noqa


# --------------------------------------------------------------------------------
class NumberPickerServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=3333)
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with NumberPickerServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
