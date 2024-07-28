import json

from ...data_transfer_objects import LogLevelRequestDto, LogLevelResponseDto, LogBufferRequestDto, LogBufferResponseDto
from ...clients.client_base import ClientBase
from ...sending.sender_base import SenderBase

# --------------------------------------------------------------------------------
class EcoLogLevelSender(SenderBase[LogLevelRequestDto, LogLevelResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(
            client,
            "eco.log.level",
            LogLevelRequestDto,
            LogLevelResponseDto
        )

    async def send(self, level: str = "debug"):
        request_data = LogLevelRequestDto(level=level)
        response     = await self.send_data(request_data)
        print("================================================================================")
        print(f"New Log Level requested: [{level}]")
        print("--------------------------------------------------------------------------------")
        print(f"{json.dumps(response.level, indent=4)}")
        print("================================================================================")

# --------------------------------------------------------------------------------
class EcoLogBufferSender(SenderBase[LogBufferRequestDto, LogBufferResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(
            client,
            "eco.log.buffer",
            LogBufferRequestDto,
            LogBufferResponseDto
        )

    async def send(self, size: int = 0):
        request_data = LogBufferRequestDto(size=size)
        response     = await self.send_data(request_data)
        print("================================================================================")
        print(f"New Log buffer size requested: [{size}]")
        print("--------------------------------------------------------------------------------")
        print(f"{json.dumps(response.size, indent=4)}")
        print("================================================================================")
