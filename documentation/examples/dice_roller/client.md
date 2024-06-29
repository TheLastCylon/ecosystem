# The Dice roller client

I believe I have effectively demonstrated that services developed using Ecosystem, can deal with TCP, UDP and UDS communications.

So, from this point on, I'll only be using TCP for the example code.

You should take note though, in terms of communication speed:
- TCP is the slowest.
- UDS is significantly faster than TCP. In my experience, about 1.5 times as fast as TCP.
  - Keep in mind that UDS can only be used by two components running on the same machine.
- UDP, at least in my experience, is close to twice as fast as UDS, when both components are running on the same machine!

I'm choosing to use TCP as the example code, simply because that's what most developers will be familiar with.

With that in mind, let's start looking at the code:

This example can be run with: `python -m examples.dice_roller.client`

Remember to have the server running with: `python -m examples.dice_roller.dice_roller_example -i 0`

## The code.

First, let's take a look at the sender package.

### The sender Python package:

#### [senders/tcp_config.py](../../../examples/dice_roller/senders/tcp_config.py)
```python
from ecosystem.clients import TCPClient

tcp_client = TCPClient(server_host='127.0.0.1', server_port=8888)
```

This is genuinely nothing more than a set-up of the `TCPClient` instance we'll be using with our senders.

#### [senders/roll.py](../../../examples/dice_roller/senders/roll.py)
```python
from ecosystem.sending import sender

from .tcp_config import tcp_client
from ..dtos import RollRequestDto, RollResponseDto


@sender(tcp_client, "dice_roller.roll", RollResponseDto)
async def sender_dice_roller_roll(sides: int):
    return RollRequestDto(sides=sides)


async def roll_a_dice(number_of_sides: int):
    print(f"roll_a_dice: number of sides[{number_of_sides}]. ", end="")
    tcp_response: RollResponseDto = await sender_dice_roller_roll(number_of_sides) # noqa
    print(f"Received: [{tcp_response.result}]")
```

In the imports we:
- get the `sender` decorator from Ecosystem.
- get our configured and instantiated `TCPClient`
- get our DTOs

Then we declare and define our sender function `sender_dice_roller_roll`.

The `roll_a_dice` function is where `sender_dice_roller_roll` is called, along with some nice output to show us what's going on during run-time.

#### [senders/guess.py](../../../examples/dice_roller/senders/guess.py)
```python
from ecosystem.sending import sender
from ecosystem.data_transfer_objects import EmptyDto

from .tcp_config import tcp_client
from ..dtos import GuessResponseDto


@sender(tcp_client, "dice_roller.guess", GuessResponseDto)
async def sender_dice_roller_guess():
    return EmptyDto()


async def do_some_guessing():
    print(f"do_some_guessing: Sending. ", end="")
    tcp_response: GuessResponseDto = await sender_dice_roller_guess() # noqa
    print(f"Received: [{tcp_response.number}]")
```

Here you'll note the import of `EmptyDto`.

As mentioned in the discussion on the server, the `guess` endpoint does not require data.
So here we use `EmptyDto` to reflect that in our sender function.

Note that all `sender_dice_roller_guess` does, is to construct an instance of `EmptyDto` and return it.

Then we create `do_some_guessing`, which does nothing more than call `sender_dice_roller_guess`, along with some nice output.

#### [senders/roll_times.py](../../../examples/dice_roller/senders/roll_times.py)
```python
from ecosystem.sending import sender
from ecosystem.data_transfer_objects import QueuedEndpointResponseDTO

from .tcp_config import tcp_client
from ..dtos import RollTimesRequestDto


@sender(tcp_client, "dice_roller.roll_times", QueuedEndpointResponseDTO)
async def sender_dice_roller_roll_times(sides: int, how_many: int):
    return RollTimesRequestDto(sides=sides, how_many=how_many)


async def roll_several_dice(sides: int, how_many: int):
    print(f"roll_several_dice: sides[{sides}] how_many[{how_many}]. ", end="")
    tcp_response = await sender_dice_roller_roll_times(sides, how_many)
    print(f"Received: [{tcp_response.uid}]")
```

In our imports, the important thing here, is the import of `QueuedEndpointResponseDTO`

This is so that our use of the `sender` decorator, can have a response DTO type to work with.

The rest is as with the previous examples:
- We create our sender function `sender_dice_roller_roll_times`, that does nothing more than instantiate an instance of `RollTimesRequestDto` and return it.
- `roll_several_dice` is where we call `sender_dice_roller_roll_times`, along with some nice output.

#### [senders/\_\_init\_\_.py](../../../examples/dice_roller/senders/__init__.py)
```python
from .guess import do_some_guessing
from .roll import roll_a_dice
from .roll_times import roll_several_dice
```

Yup, nothing special here. Just imports of some functions.

### And now the client
```python
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
```

Indeed! About as simple as one can get, right?

Just the imports for `asyncio` and the functions we created in the sender package.

Followed by the `main` function where we call the functions we created in the sender package.

And finally, the use of `asyncio.run(main())`, to run our client.

Simple and effective: The Dice roller client ... Done.
