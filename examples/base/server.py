from ecosystem import ApplicationBase, ConfigApplication, ConfigApplicationInstance, ConfigTCP, ConfigUDP, ConfigUDS

app_config          = ConfigApplication(name = "base_example")
app_instance_config = ConfigApplicationInstance(
    instance_id = "0",
    tcp         = ConfigTCP(host="127.0.0.1", port=8888),
    udp         = ConfigUDP(host="127.0.0.1", port=8889),
    uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
)
app_config.instances[app_instance_config.instance_id] = app_instance_config


# --------------------------------------------------------------------------------
class BaseServer(ApplicationBase):
    def __init__(self):
        super().__init__(app_config.name, [], app_config, '/tmp')


# --------------------------------------------------------------------------------
def main():
    app = BaseServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
