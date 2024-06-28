from ecosystem import ApplicationBase
from ecosystem import ConfigApplication
from ecosystem import ConfigApplicationInstance
from ecosystem import ConfigTCP
from ecosystem import ConfigUDP
from ecosystem import ConfigUDS

# Pycharm complains that we aren't using these imports.
# But the act of importing is what does the work we need to get done.
# So I add a noqa comment to let it know, that I know what I'm doing here.
from .handlers import ( # noqa
    dice_roller_guess,
    dice_roller_roll,
    dice_roller_roll_times
)

app_config          = ConfigApplication(name = "dice_roller_example")
app_instance_config = ConfigApplicationInstance(
    instance_id     = "0",
    tcp             = ConfigTCP(host="127.0.0.1", port=8888),
    udp             = ConfigUDP(host="127.0.0.1", port=8889),
    uds             = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
    queue_directory = "/tmp"
)
app_config.instances[app_instance_config.instance_id] = app_instance_config


# --------------------------------------------------------------------------------
class DiceRollerExampleServer(ApplicationBase):
    def __init__(self):
        super().__init__(
            app_config.name,
            app_config
        )


# --------------------------------------------------------------------------------
def main():
    with DiceRollerExampleServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
