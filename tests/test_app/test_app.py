from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS

from .endpoints import test_endpoint # noqa

# --------------------------------------------------------------------------------
class TestAppServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
        self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
        self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with TestAppServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
