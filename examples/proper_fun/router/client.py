import sys
import uuid
import asyncio
import random

from ekosis.sending.sender import sender
from ekosis.clients import UDPClient

from .dtos import RouterRequestDto, RouterResponseDto

router_client = UDPClient(server_host='127.0.0.1', server_port=8600)

MESSAGE_OPTIONS = ["fortune", "joke", "lotto", "time", "question"]

SLEEP_PERIOD = 0.1

# --------------------------------------------------------------------------------
@sender(router_client, "app.process_message", RouterResponseDto)
async def sender_app_process_message(message: str, **kwargs):
    return RouterRequestDto(request=message)

# --------------------------------------------------------------------------------
async def send_message(message: str):
    uuid_to_use = uuid.uuid4()
    print("================================================================================")
    print(f"Sending : UUID[{uuid_to_use}] message[{message}]")
    response: RouterResponseDto = await sender_app_process_message(message, request_uid=uuid_to_use) # noqa
    print("--------------------------------------------------------------------------------")
    print(f"Received: [{response.response}]")

# --------------------------------------------------------------------------------
async def main():
    global SLEEP_PERIOD
    try:
        while True:
            message = random.choice(MESSAGE_OPTIONS)
            if message == "lotto":
                number   = random.randint(1, 10)
                message += f" {str(number)}"
            await send_message(message)
            if SLEEP_PERIOD != 0:
                await asyncio.sleep(SLEEP_PERIOD)
    except Exception as e:
        print(str(e))
        return

# --------------------------------------------------------------------------------
def can_be_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# --------------------------------------------------------------------------------
try:
    if len(sys.argv) > 1:
        try:
            SLEEP_PERIOD = float(sys.argv[1])
        except ValueError:
            SLEEP_PERIOD = 0.1

    print(f"Using sleep period: {SLEEP_PERIOD}")
    asyncio.run(main())
except KeyboardInterrupt:
    print("================================================================================")
    print("\nSending done.")
