import asyncio

from .client_guess import GuessEndpointClient
from .client_roll import RollEndpointClient
from .client_roll_times import RollTimesEndpointClient


# --------------------------------------------------------------------------------
async def main():
    guess_client      = GuessEndpointClient()
    roll_client       = RollEndpointClient()
    roll_times_client = RollTimesEndpointClient()

    try:
        await guess_client.send_message()
        await roll_client.send_message(20)
        await roll_times_client.send_message(20, 10)
    except Exception as e:
        print(str(e))
        return

asyncio.run(main())
