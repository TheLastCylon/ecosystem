import uuid
from pydantic import BaseModel as PydanticBaseModel

from ecosystem import ApplicationBase
from ecosystem import ConfigApplication
from ecosystem import ConfigApplicationInstance
from ecosystem import ConfigTCP
from ecosystem import ConfigUDP
from ecosystem import ConfigUDS
from ecosystem import endpoint


# --------------------------------------------------------------------------------
class EchoRequestDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
class EchoResponseDto(PydanticBaseModel):
    message: str


# --------------------------------------------------------------------------------
@endpoint("echo", EchoRequestDto)
async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    return EchoResponseDto(message = request.message)


# --------------------------------------------------------------------------------
app_config          = ConfigApplication(name = "echo_example")
app_instance_config = ConfigApplicationInstance(
    instance_id = "0",
    tcp         = ConfigTCP(host="127.0.0.1", port=8888),
    udp         = ConfigUDP(host="127.0.0.1", port=8889),
    uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
)
app_config.instances[app_instance_config.instance_id] = app_instance_config


# --------------------------------------------------------------------------------
class EchoExampleServer(ApplicationBase):
    def __init__(self):
        super().__init__(app_config.name, app_config)


# --------------------------------------------------------------------------------
def main():
    app = EchoExampleServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e))
