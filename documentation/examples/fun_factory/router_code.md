# The Fun Factory: Router component

As stated before, the `[router]` component does quite a bit of work:

- It takes what the client sends in, maps it to the appropriate service, gets the response, then passes it back too `[client]`.
- While it is doing this:
  - It also sends message to `[tracker]`, for every message received from `[client]`.
  - Both the message received from `client` as well as the response returned to `[client]` are logged this way.
  - Because `[router]` has to respond to `[client]` as fast as possible, the work it does to notify `[tracker]` of the messages, may not interfere with its responses to `[client]`
  - Run using: `python -m examples.fun_factory.router.router -i 0`
  - The Code is located in: `examples/fun_factory/router`

## The code

The code for this can be found in the `examples/fun_factory/router/` directory, of this repository.

The relevant files for `[router]` are:
- [clients.py](../../../examples/fun_factory/router/clients.py)
- [dtos.py](../../../examples/fun_factory/router/dtos.py)
- [router.py](../../../examples/fun_factory/router/router.py)
- [senders.py](../../../examples/fun_factory/router/senders.py)
- [endpoints.py](../../../examples/fun_factory/router/endpoints.py)

Let's take a look at each of them in turn.

### [clients.py](../../../examples/fun_factory/router/clients.py)

```python
from ekosis.clients import TCPClient

fortunes_client=TCPClient("127.0.0.1", 8100)
joker_client=TCPClient("127.0.0.1", 8200)
lottery_client=TCPClient("127.0.0.1", 8300)
magic8ball_client=TCPClient("127.0.0.1", 8400)
time_reporter_client=TCPClient("127.0.0.1", 8500)
tracker_client=TCPClient("127.0.0.1", 8700)
```

There is nothing special here. Just setup of clients that will be used with the `sender` and `queued_sender` decorator, in [senders.py](../../../examples/fun_factory/router/senders.py)

### [dtos.py](../../../examples/fun_factory/router/dtos.py)
```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RouterRequestDto(PydanticBaseModel):
    request: str


# --------------------------------------------------------------------------------
class RouterResponseDto(PydanticBaseModel):
    response: str
```

Again, nothing you've not seen in previous examples. Just some DTOs we'll be using with the `endpiont` decorator in [endpoints.py](../../../examples/fun_factory/router/endpoints.py)

### [router.py](../../../examples/fun_factory/router/router.py)

```python
from ekosis.application_base import ApplicationBase
from ekosis.configuration.config_models import ConfigTCP

from .endpoints import process_message  # noqa


# --------------------------------------------------------------------------------
class RouterServer(ApplicationBase):
    def __init__(self):
        self._configuration.tcp=ConfigTCP(host="127.0.0.1", port=8600)
        self._configuration.queue_directory='/tmp'
        self._configuration.stats_keeper.gather_period=60
        self._configuration.stats_keeper.history_length=60
        super().__init__()


# --------------------------------------------------------------------------------
def main():
    with RouterServer() as app:
        app.start()


# --------------------------------------------------------------------------------
if __name__=='__main__':
    main()
```

And here's the server, as you've seen in previous examples.

Noteworthy things here are:
- The import of `process_message` from `endpoints`.
- The configuration, where we set the queue directory for the `[router]` application.
- Remember, if you are using Windows, you'll have to change that to a usable location on your system.

Now we start getting to the guts of this, lets take a look at [senders.py](../../../examples/fun_factory/router/senders.py).

### [senders.py](../../../examples/fun_factory/router/senders.py) 

#### The imports

```python
from ekosis.sending.sender import sender
from ekosis.sending.queued_sender import queued_sender
from ekosis.data_transfer_objects import EmptyDto, QueuedEndpointResponseDTO
```
You know about `EmptyDto`, `QueuedEndpointResponseDTO` and the `sender` decorator already.

What you've not seen up until now is, `queued_sender`. We'll explore that a bit further down.

```python
from ..fortunes.dtos import FortuneResponseDto
from ..joker.dtos import JokerResponseDto
from ..lottery.dtos import NumberPickerRequestDto, NumberPickerResponseDto
from ..magic_eight_ball.dtos import Magic8BallRequestDto, Magic8BallResponseDto
from ..time_reporter.dtos import CurrentTimeResponseDto
from ..tracker.dtos import TrackerLogRequestDto
```

Here we get all the DTOs we'll need for the `[fortunes]`, `[joker]`, `[lottery]`, `[magic_eight_ball]`, `[time_reporter]` and `[tracker]` components.

```python
from .clients import (
    fortunes_client,
    joker_client,
    lottery_client,
    magic8ball_client,
    time_reporter_client,
    tracker_client
)
```

Here we import the clients we want to use with our various senders.

#### The senders
```python
# --------------------------------------------------------------------------------
@sender(fortunes_client, "app.get_fortune", FortuneResponseDto)
async def get_fortune(*args, **kwargs):
    return EmptyDto()


# --------------------------------------------------------------------------------
@sender(joker_client, "app.get_joke", JokerResponseDto)
async def get_joke(*args, **kwargs):
    return EmptyDto()


# --------------------------------------------------------------------------------
@sender(lottery_client, "app.pick_numbers", NumberPickerResponseDto)
async def pick_numbers(how_many: int = 1, *args, **kwargs):
    return NumberPickerRequestDto(how_many=how_many)


# --------------------------------------------------------------------------------
@sender(magic8ball_client, "app.get_prediction", Magic8BallResponseDto)
async def get_prediction(question: str, *args, **kwargs):
    return Magic8BallRequestDto(question=question)


# --------------------------------------------------------------------------------
@sender(time_reporter_client, "app.get_time", CurrentTimeResponseDto)
async def get_time(*args, **kwargs):
    return EmptyDto()
```

You'll notice something a little different with how we define our functions here.
Can you spot it?

Have you noticed that each one of them now caters for `*args` and `**kwargs`?

Yea, we'll be doing something special with that further down. Just keep it in mind for now.

#### The Queued senders
```python
# --------------------------------------------------------------------------------
@queued_sender(
    tracker_client,
    "app.log_request",
    TrackerLogRequestDto,
    QueuedEndpointResponseDTO,
    0,
    1000,
    10
)
async def log_request(data: str, timestamp: float, *args, **kwargs):
    return TrackerLogRequestDto(
        request   = data,
        timestamp = timestamp
    )


# --------------------------------------------------------------------------------
@queued_sender(
    tracker_client,
    "app.log_response",
    TrackerLogRequestDto,
    QueuedEndpointResponseDTO,
    0,
    1000,
    10
)
async def log_response(data: str, timestamp: float, *args, **kwargs):
    return TrackerLogRequestDto(
        request   = data,
        timestamp = timestamp
    )
```

Now this, you have not seen in previous examples. Rest assured though, they are
basically the same as `queued_endpoint`, just from the sending side, as apposed
to receiving.

`queued_sender` needs at least 4 things from you:
1. An instantiated client you want to use for sending.
2. The route key used on the server side, that you want to send your message to.
3. A request dto type
4. A response dto type.

The other parameters you can set are:
1. `wait_period`:
   - A floating point value, indicating the number of seconds or fractions of a second,
     you want the sender process to wait between sending messages. In the example, we
     set it to `0`. The default for this is also `0`.
2. `max_uncommited`:
   - As discussed in the
     [technical stuff for `queued_endpoint`](../../queueds/technical_stuff.md),
     this tells each of the sql databases for your queues, how many inserts and deletes
     it should allow, before doing a commit. For this example, I set it to `1000`. The
     default for this is `0`
3. `max_retries`:
   - Again, as discussed in
     [technical stuff for `queued_endpoint`](../../queueds/technical_stuff.md),
     this tells Ecosystem how many times it should try sending a message, before giving
     up on it and moving it to the `error` database of the queue.
   - It's important to note, that Ecosystem will only retry sending, if it makes
     sense to retry. In other words, for almost all cases other than the server being
     busy, the message will be moved to the `error` database.
   - As for `queued_endpoint`, Ecosystem already has all the functionality you need to
     do things like:
     - Inspect the queues
     - Get statistical information on the queues
     - Re-process entries in the error database of a queue, etc, etc, etc.
     - Yes, in the event that the server you are trying to contact is down, you'll be
       able to re-process messages when it comes back up again.
     - Right now, this requires human intervention. When I get around to it though,
       Ecosystem will be enhanced to do this for you, automatically.
   - In the example, I set it to `10`, but the default is `0`.

Let us take a look at one of these `queued_senders` though:
```python
@queued_sender(
    tracker_client,
    "app.log_request",
    TrackerLogRequestDto,
    QueuedEndpointResponseDTO,
    0,
    1000,
    10
)
async def log_request(data: str, timestamp: float, *args, **kwargs):
    return TrackerLogRequestDto(
        request   = data,
        timestamp = timestamp
    )
```

Here we are setting this `queueud_sender` to:
- Use the client we instantiated called `tracker_client`
- Send messages to the `app.log_request` endpoint of the `[tracker]` service.
- Use `TrackerLogRequestDto` and `QueuedEndpointResponseDTO` as our request and
  response DTOs
- Have a `wait_period` of `0` seconds between sending messages.
- Have a maximum of `1000` inserts and deletes on the queue databases.
- And retry no more than `10` times.

As for the `log_request` function we are defining, take a look at the signature.

```python
async def log_request(data: str, timestamp: float, *args, **kwargs):
```

Strictly speaking, we don't need to specify `*args` or `**kwargs`, but we are
doing something special here, that will become clear in our discussion on the
endpoints for `[router]`. Keep it in mind.

All this function does, is to instantiate an instance of our request dto,
`TrackerLogRequestDto`, and return it. The functions you create for your
project, will have to do the same in terms of what it returns.

Now let us take a look at the endpoints. This, is where the interesting stuff happens.

### [endpoints.py](../../../examples/fun_factory/router/endpoints.py)

---
#### The imports

```python
import uuid
import logging
import time

from typing import cast, List
from pydantic import BaseModel as PydanticBaseModel

from ekosis.requests.endpoint import endpoint
from ekosis.util.fire_and_forget_tasks import run_soon

from .dtos import RouterRequestDto, RouterResponseDto

from .senders import (get_fortune, get_joke, pick_numbers, get_prediction, get_time, log_request, log_response)
```

Everything up to the import for `run_soon`, you have seen before. We'll get to looking at `run_soon` ... Soon. `:)`

After that import, we simply import our DTOs and then our various senders.

---
### The `endpoint` or rather: How to use `request_uuid` to save you both time and money

Before we get to the varius helper functions and what they do, take a look at the `process_message` function that we decorate with `endpoint`.

```python
# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    request_data_raw = cast(RouterRequestDto, request)
    _log_request(request_uuid, request_data_raw.request, time.time())
    log.info(f"RCV: request_uuid[{request_uuid}]")
    request_data = request_data_raw.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(request_uuid)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(request_uuid)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(request_uuid, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(request_uuid)
    else:
        response = await _get_prediction(request_uuid, request_data_raw.request)

    log.info(f"RSP: request_uuid[{request_uuid}]")
    _log_response(request_uuid, response, time.time())
    return RouterResponseDto(response=response)
```

---
#### Using `request_uuid` and the implications thereof.

Unlike previous examples, you'll notice we are actually using `request_uuid` this time.

Ecosystem invokes your `endpoint` functions, with that as a parameter. It
literally contains the protocol level UUID, of the request your function is
invoked to process.

This is also the same UUID used, in both the `pending` and `error` databases,
created when you use `queued_endpoint` and `queued_sender`.

If you are paying attention, you might begin to see the **real-world** implications
of this, and why I designed Ecosystem to facilitate it.

Before we get into that though, lets take a look at one of the helper functions:

```python
# --------------------------------------------------------------------------------
async def _get_fortune(uid: uuid.UUID) -> str:
    return (await get_fortune(request_uid=uid)).fortune
```

I arbitrarily selected `_get_fortune` for this, it really is just the first one
I got my hands on for what I'm about to discuss. All of this, also applies to:
`_get_joke`, `_get_lotto`, `_get_time` and `_get_prediction`. These helper
functions are really just there to keep the code neat. The important
bit is how we invoke our sender functions from them.

Take a look at how we are invoking our sender function `get_fortune`.

```python
    return (await get_fortune(request_uid=uid)).fortune
```

We are passing it, the UUID of the request we received, as a key-word argument `request_uid`.

This is why our sender functions were defined to have `*args` and `**kwargs`

Doing this, causes Ecosystem to use the UUID we specify, as the UUID for the request
it makes to the `[fortunes]` service.

The real-world effect of this is:
- `[client]`, `[router]`, `[fortunes]` and `[trakcer]` are all using the same
  UUID for an **entire** communications chain!
- The logs created, all log the exact same UUID, for the **entire** communications
  chain.

If you get it now, you have very likely spent hours pouring over logs of a
distributed system. You possibly even resorted to putting your logs in some
searchable database, so you can try to figure out where things are going wrong.
Some of you may even have resorted to using 3rd party services for this.

With Ecosystem, if you apply this little bit of effort, and combine it with logging.
You can achieve all of that, with a single `grep`, `awk` or `ag` command.

That means: All of that log searching ability ... For free.

And yes, that is for free as in: "Free pizza"!

In fact, the `[tracker]` component of this example, is an effective equivalent,
of one of those 3rd party services you would normally spend your money on.

You're welcome! It's my pleasure, I assure you.

Now lets take a look at what `run_soon` is all about.

---
### `run_soon`? Why not run now?

As mentioned before, `[router]` sends messages to `[traker]`, causing it to
keep record of the requests from and the responses to `[client]`.

Thing is, in a real world scenario like this example emulates, `[router]` must
respond to `[client]` as fast as possible. So it's interaction with `[tracker]`
may not slow it down in that respect.

Let's take a look at what the endpoint function does, again:

```python
# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    request_data_raw = cast(RouterRequestDto, request)
    _log_request(request_uuid, request_data_raw.request, time.time())
    log.info(f"RCV: request_uuid[{request_uuid}]")
    request_data = request_data_raw.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(request_uuid)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(request_uuid)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(request_uuid, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(request_uuid)
    else:
        response = await _get_prediction(request_uuid, request_data_raw.request)

    log.info(f"RSP: request_uuid[{request_uuid}]")
    _log_response(request_uuid, response, time.time())
    return RouterResponseDto(response=response)
```

Notice the invocations of:
```python
    _log_request(request_uuid, request_data_raw.request, time.time())
```

and

```python
    _log_response(request_uuid, response, time.time())
```

Now also take a look at the definitions for those functions:
```python
# --------------------------------------------------------------------------------
@run_soon
async def _log_request(uid: uuid.UUID, data: str, timestamp: float):
    await log_request(data, timestamp, request_uid=uid)


# --------------------------------------------------------------------------------
@run_soon
async def _log_response(uid: uuid.UUID, data: str, timestamp: float):
    await log_response(data, timestamp, request_uid=uid)
```

You'll note your IDE and/or linting tools will be screaming about where
those functions are invoked. It will tell you all about your Coroutine not
being awaited.

My advice: Hand it a pill and tell it to chill!

Or as the new generation will say: Leave it on read.

Neither IDEs nor Linting tools have the ability to track what Ecosystem is doing
here. They will catch up. Eventually. It really isn't anything special or
complicated. You could achieve the same with a little bit of research into
`asyncio` and python decorators.

Enough about that though.

When you decorate a function with `run_soon`, you are telling the python
interpreter and `asyncio` that:

When I invoke this function, schedule it for execution AFTER the function I
make the call from, exits.

In other words:
Please run this function, some time after I'm done doing my work here.

It is just a way to do "fire-and-forget", or "do-something" functions.

Note that you do not have to write any code to interact with `asyncio` or the
event loop.

`run_soon` takes care of that for you.

As promised, Ecosystem does the heavy lifting with respect to `asyncio`, for you.

---
### The rest of it

The rest of what the `process_message` endpoint function does, is really just
mapping the received request to a function call, that becomes a request to one
of the services. Then taking the response from that service, and returning it to
`[client]`

All of this was really just to teach you about:
1. Using `request_uuid` to make your life easier when it comes to doing investigations.
2. How to use `queued_sender` and
3. What `run_soon` does for you.

By the time you have gotten a grip on this example, and what it does, you'll have all
the tools you need to start creating your own distributed systems, using Ecosystem.

You are most welcome. I assure you, the pleasure is all mine!

Ecosystem isn't so much for all of you out there, as it is for: ME!

I wanted this, so I built it.
