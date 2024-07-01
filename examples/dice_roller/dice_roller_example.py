from ecosystem.application_base import ApplicationBase
from ecosystem.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS

# Pycharm complains that we aren't using these imports.
# But the act of importing is what does the work we need to get done.
# So I add a noqa comment to let it know, that I know what I'm doing here.
from .handlers import ( # noqa
    dice_roller_guess,
    dice_roller_roll,
    dice_roller_roll_times
)


# --------------------------------------------------------------------------------
class DiceRollerExampleServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp             = ConfigTCP(host="127.0.0.1", port=8888)
        self._configuration.udp             = ConfigUDP(host="127.0.0.1", port=8889)
        self._configuration.uds             = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
        self._configuration.queue_directory = "/tmp"
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with DiceRollerExampleServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
