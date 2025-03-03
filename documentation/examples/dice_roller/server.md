# Dice roller Server

## The Code

### [dice_roller_example.py](../../../examples/dice_roller/dice_roller_example.py)

```python
from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS

# Pycharm complains that we aren't using these imports.
# But the act of importing is what does the work we need to get done.
# So I add a noqa comment to let it know, that I know what I'm doing here.
from .handlers import (  # noqa
    dice_roller_guess,
    dice_roller_roll,
    dice_roller_roll_times
)


# --------------------------------------------------------------------------------
class DiceRollerExampleServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp=ConfigTCP(host="127.0.0.1", port=8888)
        self._configuration.udp=ConfigUDP(host="127.0.0.1", port=8889)
        self._configuration.uds=ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
        self._configuration.queue_directory="/tmp"
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with DiceRollerExampleServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__=='__main__':
    main()
```

The code here has nothing we have not covered in our previous examples. All that's truly worthy of any amount of attention, is the fact that our endpoints are now in a Python package called `handlers`.

Therefore, you'll note the import statement:
```python
from .handlers import ( # noqa
    dice_roller_guess,
    dice_roller_roll,
    dice_roller_roll_times
)
```

As stated in the comment in the code. The Pycharm `# noqa` comment is there to get Pycharm to stop complaining about the fact, that the imported items aren't used in the source for `server.py`

As stated there, the act of importing it, is what does the work we need done. If you aren't using Pycharm, you might have to do the equivalent for what ever IDE you are using.

Let's move on and take a look at the endpoints.

### The endpoints

#### [handlers/roll.py](../../../examples/dice_roller/handlers/roll.py)

```python
 1: import uuid
 2: import logging
 3: import random
 4: 
 5: from pydantic import BaseModel as PydanticBaseModel
 6: 
 7: from ekosis.requests.endpoint import endpoint
 8: 
 9: from ..dtos import RollRequestDto, RollResponseDto
10: 
11: logger = logging.getLogger()
12: 
13: @endpoint("dice_roller.roll", RollRequestDto)
14: async def dice_roller_roll(uid: uuid.UUID, dto: RollRequestDto) -> PydanticBaseModel:
15:     logger.debug(f"dice_roller_roll 000 [{dto}]")
16:     numbers = list(range(1, dto.sides))
17:     return RollResponseDto(result = random.choice(numbers))
```

Here you'll note that we import our DTOs in:
```python
from ..dtos import RollRequestDto, RollResponseDto
```

The endpoint itself does nothing more than:
1. Accept a request of type `RollRequestDto`
2. On a route key named `dice_roller.roll`
3. Then generates a random selection from a list. The list itself is just a collection
   of integers, the amount of them being determined by the value of `dto.sides`, and then places the result in a response of type `RollResponseDto`

So yea, we roll a die, having sides equal to the number specified by the value of `dto.sides`.

The only thing really worthy of note here, is the route key: `dice_roller.roll`.

See the `.` character in `dice_roller.roll`?

Keep that in mind. It is one of the things you can do to "play-nice" with Ecosystem. When we get to talking about all the goodies one gets with Ecosystem, we'll cover this particular ... point.

Yes, of course that pun was on purpose! :D

#### [handlers/guess.py](../../../examples/dice_roller/handlers/guess.py)

```python
1: import uuid
2: import logging
3: import random
4:
5: from typing import List
6: from pydantic import BaseModel as PydanticBaseModel
7:
8: from ekosis.requests.endpoint import endpoint
9:
10: from ..dtos import GuessResponseDto
11:
12: logger = logging.getLogger()
13:
14: @endpoint("dice_roller.guess")
15: async def dice_roller_guess(**kwargs) -> PydanticBaseModel:
16:     numbers: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
17:     return GuessResponseDto(number = random.choice(numbers))
18:
```

Here we import our request dto with:

```python
from ..dtos import GuessResponseDto
```

And declare our endpoint with:

```python
@endpoint("dice_roller.guess")
async def dice_roller_guess(**kwargs) -> PydanticBaseModel:
    numbers: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return GuessResponseDto(number = random.choice(numbers))
```

Remember when we looked at the dtos earlier, you might have noticed there's no request dto in [dtos/guess.py](../../../examples/dice_roller/dtos/guess.py)?

This is why!

Take a look at our use of the `endpoint` decorator there.

Notice that we aren't specifying a request DTO.

When we do this, we are basically saying: This endpoint does not need data.

Typically, one would use something like this, when all the server needs to know, is that the endpoint was called.

Behind the scenes, Ecosystem sets the request DTO to `EmptyDTO`, declared in `ekosis/data_transfer_objects/empty.py`

It looks like this:
```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class EmptyDto(PydanticBaseModel):
    pass
```

Yes, it literally is an empty class derived from Pydantic's `BaseModel` class.

Remember this class, we'll be referring to it again when we talk about the dice roller client.

For now though, let's move on to the last endpoint.

#### [handlers/roll_times.py](../../../examples/dice_roller/handlers/roll_times.py)

Before you look at the code below, I'd like to welcome you to the world of: QUEUED endpoints.

"What the heck is that?!", you ask.

Well, think about this scenario:

1. You have a client, or even several clients, that need to dump quite a few notifications at a server's door.
2. These clients don't need to get the result of what was done, they just need the server to know that it has to DO something. And perhaps notify them later.
3. Thing is, during peak times, your server gets absolutely thrashed with requests. And trying to process these requests, build responses and give data back to the client ... Yea, that slows your server down to a crawl, doesn't it?

Now, a currently standard industry solution would include things like:
1. A queueing service of some kind.
2. A load balancer.
3. Etc. etc. etc.

This means you have to pay for hosting, possibly have some expert hired to configure stuff, document its use and purpose, along with a lot of "after-the-fact" costs of maintaining the solution.

Thing is, in my experience at least, peak times seldom last more than a few minutes, half an hour at a stretch, an hour tops. On top of all this, the fact that as long as the work gets done, no one really cares. Means a stack of money ends up being spent on what could be solved in 5 minutes, with nothing more than a few lines of code.

Enter ... the Ecosystem QUEUED endpoint!


IMPORTANT!

This is NOT a silver bullet, or in any way a means of totally avoiding having to put load-balancers or carrier-grade queueing solutions in place.

It is however, a solution that fills the gap between not needing carrier-grade solutions, and factually having to hand over cash for them.

For more on this, take a look at the documentation for:
- [Queued endpoints](../../queueds/queued_endpoints.md) and
- [Queued endpoints, the technical stuff](../../queueds/technical_stuff.md)

Let us move on with this example though.

```python
 1: import uuid
 2: import asyncio
 3: import random
 4: import logging
 5:
 6: from ekosis.requests.queued_endpoint import queued_endpoint
 7:
 8: from ..dtos import RollTimesRequestDto
 9:
10:
11: @queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
12: async def dice_roller_roll_times(uid: uuid.UUID, dto: RollTimesRequestDto) -> bool:
13:     log     = logging.getLogger()
14:     numbers = list(range(1, dto.sides))
15:
16:     log.info(f"roll_times[{uid}]: Processing.")
17:     total_result   = 0
18:     expected_total = (dto.sides*dto.how_many)*0.6
19:     for times in range(dto.how_many):
20:         total_result += random.choice(numbers) + 1
21:
22:     log.info(f"roll_times[{uid}]: expected_total[{expected_total}] total_result[{total_result}]")
23:     if total_result < expected_total:
24:         log.info(f"roll_times[{uid}]: FAIL!")
25:         await asyncio.sleep(1)
26:         return False
27:
28:     log.info(f"roll_times[{uid}]: Success.")
29:     await asyncio.sleep(1)
30:     return True
31:
```

For now, and for this example, all you really need to know is:

- We import our request DTO with:
```python
from ..dtos import RollTimesRequestDto
```

- We decorate a function that processes queued requests with:

```python
@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
```

Just like the normal `endpoint`, a `queued_endpoint` needs:
1. A route key
2. A request DTO Type

- Then we proceed to declare and define the processor function.

If you've been paying attention, you'll notice that the function we declared there, returns a bool. NOT a response DTO.

The response DTO of a `queued_endpoint`, is always `QueuedEndpointResponseDTO`.

It is declared in `ekosis/data_transfer_objects/queued_endpoint_response.py` and looks like this:

```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class QueuedEndpointResponseDTO(PydanticBaseModel):
    uid: str
```

The content of uid that you get in this response, is the uid of the JSON request that the server received. For more on that, look at [the protocol](../../the_protocol.md).

And this is the point at which we answer the question:

"Why is there no response DTO in [dtos/roll_times.py](../../../examples/dice_roller/dtos/roll_times.py)?"

The answer of course is:

Because the response DTO for a queued endpoint, is already defined!

It is: `QueuedEndpointResponseDTO`

## Conclusion

All of the above boils down to three things you need to understand at this stage:
1. Most of the time, you'll need two DTOs: A request and response DTO.
2. Some of the time you'll use `EmptyDTO` as your request DTO.
3. Yet fewer times you'll have only a request DTO, and use `QueuedEndpointResponseDTO` for the response.

Now, let's move on and look at the [client](./client.md).
