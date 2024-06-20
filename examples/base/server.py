from ecosystem import ApplicationBase
from ecosystem import ConfigApplication
from ecosystem import ConfigApplicationInstance
from ecosystem import ConfigTCP
from ecosystem import ConfigUDP
from ecosystem import ConfigUDS

app_config          = ConfigApplication(name = "base_example")
app_instance_config = ConfigApplicationInstance(
    instance_id = "0",
    tcp         = ConfigTCP(host="127.0.0.1", port=8888),
    udp         = ConfigUDP(host="127.0.0.1", port=8889),
    uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
)
app_config.instances[app_instance_config.instance_id] = app_instance_config


# --------------------------------------------------------------------------------
class BaseExampleServer(ApplicationBase):
    def __init__(self):
        super().__init__(app_config.name, [], app_config)


# --------------------------------------------------------------------------------
def main():
    app = BaseExampleServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
