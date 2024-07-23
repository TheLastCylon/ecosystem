# Queues, the technical stuff.

You might want to take a look at the [Ecosystem Queues, Questions and Answers](./questions_and_answers.md) first.

If you're ready to move on though, lets take a look at some code:

## A queued endpoint:

```python
from ekosis.requests.queued_endpoint import queued_endpoint


@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
```

Here you see me create a `queued_endpoint`
- with `route_key` set to `dice_roller.roll_times`
- and `request_dto_type` set to `RollTimesRequestDto`

Yes, that is all you need to create a `queued_endpoint`.

This is however, definitely NOT all you should do.

`queued_endpoint` can accept two more parameters, they are:
- `page_size` and,
- `max_retries`

For anything beyond example code, you really should take the time to **think** about
what you should set these parameters too.

---
### `page_size`

This tells each of the queue database managers, how big the front and back page
for your queues, should be. The front pages is where messages are popped from,
the back page is where messages are pushed too. Both pages exist purely in RAM.

That means:

When the back page becomes larger than the number of entries you specify, it is
written to the database file. When the front page has `0` entries in it, the
first `page_size` records in the database, are LOADED and DELETED from the
database. If there is nothing in the database, then the front, and back page,
become the same thing.

The default for `page_size`, is `100`.

This means:

If you just accept the default settings, the [Sqlite](https://sqlite.org)
database file is written too, when the back page of the queue, is about to
have more than 100 entries.

In your real-world applications, this might be far lower than what you need.

**Remember**: In terms of time, I/O operations on a computer, are one of the most
expensive things you can do.

The next thing to consider is of course: **Risk to the business**.

But before I move on with this, I want to bring to your attention that:

Even in the event of a process-terminating exception, an Ecosystem application
will shut down its queues. Causing both the front and back page to be written
to the respective database file.

So, when I use the phrase "catastrophic failure" below, it means:

A catastrophic failure involving OS or hardware. Something like an OS level
system crash, needing a machine reboot to restore. Not some miss-guided code
causing a mere exception to be thrown.

And yes, an Ecosystem application will still do this, even when it receives the
termination signals SIGTERM, SIGINT or SIGHUP. So yes, it is completely safe to
terminate a running instance of an Ecosystem application with the `kill` command.

Of course, SIGKILL can't be handled programmatically at all, so if you use either
`kill -9 <PID>` or `kill -KILL <PID>` on an Ecosystem application, you
**will lose** the data in the front and back page of your queue.

Knowing all that though, let's look at: **Risk to the business**:

When you set `page_size` to a value of `100`, what you are saying in terms
of a business is:

In the event of catastrophic failure, I'm okay with loosing `200` messages in
this queue.

So, take the time and: **Think** about what you'll need.

With this, put on your "I-am-a-responsible-Software-Engineer-hat", not the "Lazy-developer-hat".

In short:
- Be responsible.
- Be accountable.
- Keep your code sane!

---
### `max_retries`

For this, let's take a look at the dice roller example's [`roll_times`](../../examples/dice_roller/handlers/roll_times.py) `queued_endpoint` again.

```python
import uuid
import asyncio
import random
import logging

from ekosis.requests import queued_endpoint

from ..dtos import RollTimesRequestDto


@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
async def dice_roller_roll_times(request_uuid: uuid.UUID, request: RollTimesRequestDto) -> bool:
    log=logging.getLogger()
    numbers=list(range(1, request.sides))

    log.info(f"roll_times[{request_uuid}]: Processing.")
    total_result=0
    expected_total=(request.sides*request.how_many)*0.6
    for times in range(request.how_many):
        total_result+=random.choice(numbers)+1

    log.info(f"roll_times[{request_uuid}]: expected_total[{expected_total}] total_result[{total_result}]")
    if total_result<expected_total:
        log.info(f"roll_times[{request_uuid}]: FAIL!")
        await asyncio.sleep(1)
        return False

    log.info(f"roll_times[{request_uuid}]: Success.")
    await asyncio.sleep(1)
    return True
```

The `dice_roller_roll_times` function I define there, returns a boolean, and
only a boolean.

Yours has to do this too!

Ecosystem uses this return, to tell it that things have gone as you want them to 
go (`return True`), or that the request should be re-tried later (`return False`).

`max_retries` tells Ecosystem how many times these requests may be retried,
before it is placed in the error queue database.

By default, `max_retries` is set to `0`, as in: Don't retry, just do it once and
only once.

Yes, there are ways for you to inspect what is in the error queue database, and
even move items back into the incoming queue database, at runtime, from outside
your application.

You can learn more about that if you look at: [Standard endpoints for queue management](./standard_endpoints_for_management.md)

---
## A queued sender

Here you are looking at one of the `queued_sender` functions used in the
[Fun Factory example system](../examples/fun_factory/fun_factory.md).

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
```

You'll note there are a few more parameters begin set here. All you absolutely
have to give the `queued_sender` decorator is:

1. An instantiated client you want to use for sending.
2. The route key used on the server side, that you want to send your message to.
3. A request dto type
4. A response dto type.

The function you decorate with this, has to return an object of the type you
specify as the request dto type. In the case of the example code, that is
`TrackerLogRequestDto`

The response dto type is used internally, by Ecosystem, to do checks and
verifications with respect to communication. That means: It makes sure the server
did not respond with some kind of error.

Then there are three more thing you can set.
- `wait_period`,
- `page_size` and,
- `max_retries`

---
### `wait_period`
This is a floating point value, that tells Ecosystem how many seconds or
fractions of a second, you want the sender process to wait between sending
messages. In the example, we set it to `0`. The default for this is also `0`.

Yes, this is one way you can manage load to a server, from the client side.

---
### `page_size`
Is **exactly** the same as described for `queued_endpoint` above.

---
### `max_retries`
This tells Ecosystem how many times it should try sending a message, before
giving up on it and moving it to the `error` database of the queue.

- It's important to note, that Ecosystem will only retry sending, if it makes
  sense to retry. In other words, for almost all cases other than the server being
  busy, the message will be moved to the `error` database.
- In the example, I set it to `10`, but the default is `0`.
- Yes, you can re-process entries in the `error` database of a queue.
  - In the event that the server you are trying to contact is down, you'll be
    able to re-process messages when it comes back up again.
  - Right now, this requires human intervention. When I get around to it though,
    Ecosystem will be enhanced to do this for you, automatically.
