import logging
import uuid

from pydantic import BaseModel as PydanticBaseModel

from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS
from ekosis.requests.endpoint import endpoint

from .dtos import PingRequestDto, PongResponseDto

log = logging.getLogger()

# --------------------------------------------------------------------------------
@endpoint("app.ping", PingRequestDto)
async def app_ping(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    log.info(f"{request_uuid}")
    return PongResponseDto(message="pong")

# --------------------------------------------------------------------------------
class PongServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
        self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
        self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with PongServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e))
