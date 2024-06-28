import asyncio

from .senders import (
    do_some_guessing,
    roll_a_dice,
    roll_several_dice
)


# --------------------------------------------------------------------------------
async def main():
    try:
        await do_some_guessing()
        await roll_a_dice(20)
        await roll_several_dice(20, 10)
    except Exception as e:
        print(str(e))
        return


# --------------------------------------------------------------------------------
asyncio.run(main())
