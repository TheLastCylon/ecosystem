import uuid
from pydantic import BaseModel as PydanticBaseModel

from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS
from ekosis.requests.endpoint import endpoint

from .dtos import EchoRequestDto, EchoResponseDto


# --------------------------------------------------------------------------------
@endpoint("echo", EchoRequestDto)
async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    return EchoResponseDto(message = request.message)


# --------------------------------------------------------------------------------
class EchoExampleServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
        self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
        self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with EchoExampleServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e))
