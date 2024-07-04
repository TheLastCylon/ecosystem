# Queued endpoints, the technical stuff.

You might want to take a look at the [`queued_endoint` Q&A](./questions_and_answers.md) first.

If you're ready to move on, lets take a look at some code:

## The code:
```python
from ecosystem.requests import queued_endpoint

@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
```

Here you see me create a `queued_endpoint`
- with `route_key` set to `dice_roller.roll_times`
- and `request_dto_type` set to `RollTimesRequestDto`

Yes, that is all you need to create a `queued_endpoint`.

This is however, definitely NOT all you should do.

`queued_endpoint` can accept two more parameters, they are:
- `max_uncommited` and,
- `max_retries`

For anything beyond example code, you really should take the time to **think** about
what you should set these parameters too.

---
### `max_uncommited`

This tells each of the sql databases for your queues, how many inserts and
deletes it should allow, before doing a commit.

That means:

When (inserts + deletes) >= `max_uncommited`, write to the database file.

This is important, as sqlite does not write to a database file, until you do
either a commit or a flush. In the case of Ecosystem, only commits are used.

The default for `max_uncommited`, is `0`.

This means:

If you just accept the default settings, the sqlite file is written too, every
single time an entry is either pushed or popped on it.

In your real-world applications, this is highly unlikely to be what you want.

Remember: In terms of time, I/O operations on a computer, are one of the most
expensive things you can do.

So, you really want to strike a balance between having your queue databases in
RAM, and having them written to a storage device.

Also, in the long term, using the defaults won't just be bad for the speed of your
application, the life-span of your storage devices could be affected as well.

The next thing to consider is of course: Risk to the business.

When you set `max_uncommited` to a value of `100`, what you are saying in terms
of a business is:

In the even to of catastrophic failure, I'm okay with loosing `100` of the
messages in this queue.

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

from ecosystem.requests import queued_endpoint

from ..dtos import RollTimesRequestDto


@queued_endpoint("dice_roller.roll_times", RollTimesRequestDto)
async def dice_roller_roll_times(request_uuid: uuid.UUID, request: RollTimesRequestDto) -> bool:
    log     = logging.getLogger()
    numbers = list(range(1, request.sides))

    log.info(f"roll_times[{request_uuid}]: Processing.")
    total_result   = 0
    expected_total = (request.sides * request.how_many)*0.6
    for times in range(request.how_many):
        total_result += random.choice(numbers) + 1

    log.info(f"roll_times[{request_uuid}]: expected_total[{expected_total}] total_result[{total_result}]")
    if total_result < expected_total:
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
## Standard endpoints, for queued endpoint management:

Ecosystem provides a host of standard endpoints ripe and ready for you to use,
when you need to get down and dirty with queues.

They are:
- `eco.queued_handler.data`
- `eco.queued_handler.receiving.pause`
- `eco.queued_handler.receiving.unpause`
- `eco.queued_handler.processing.pause`
- `eco.queued_handler.processing.unpause`
- `eco.queued_handler.all.pause`
- `eco.queued_handler.all.unpause`
- `eco.queued_handler.errors.get_first_10`
- `eco.queued_handler.errors.reprocess.all`
- `eco.queued_handler.errors.clear`
- `eco.queued_handler.errors.reprocess.one`
- `eco.queued_handler.errors.pop_request`
- `eco.queued_handler.errors.inspect_request`


--------------------------------------------------------------------------------

