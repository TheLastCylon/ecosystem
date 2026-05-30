# Running background tasks with `setup_tasks`

## The problem it solves.

Some applications need long-running background tasks that start with the
application and run alongside its endpoints for as long as the application
is up.

A delivery worker. A cache-warming loop. A periodic cleanup job. Anything
that needs to be running before the first request arrives and stay running
until the application shuts down.

Ecosystem's event loop starts inside `app.start()`. That means you cannot
use `asyncio.create_task()` before that point -- there is no loop yet to
create a task on.

`setup_tasks` is the hook that solves this. It is called from inside the
running event loop, just before `asyncio.gather()` takes over. Your tasks
are added to the same gather that manages all of Ecosystem's internal tasks,
which means they participate fully in the application lifecycle -- started
with the application, stopped with the application.

**Fair Warning:** With `setup_tasks` you are taking on a layer of responsibility
with respect to exception handling in your tasks. If your task throws an unhandled
exception, the application will exit. There are many cases where this is desired
behavior. So rather than dictate what you should and should not expect from
your applications, EcoSystem provides this for your use but also leaves you to
take responsibility for exception handling.

---

## How to use it.

Override `setup_tasks` in your `ApplicationBase` subclass:

```python
import asyncio
from ekosis.application_base import ApplicationBase

async def my_background_task():
    while True:
        # do work
        await asyncio.sleep(1)

class MyServer(ApplicationBase):
    def __init__(self):
        super().__init__()

    async def setup_tasks(self, tasks: list):
        tasks.append(asyncio.create_task(my_background_task()))

def main():
    with MyServer() as app:
        app.start()

if __name__ == '__main__':
    main()
```

That is all there is to it. `my_background_task` will be running before the
first request reaches any of your endpoints.

---

## A note on task lifecycle.

Tasks added via `setup_tasks` are passed to `asyncio.gather()` along with
all of Ecosystem's internal tasks -- the TCP server, UDP server, UDS server,
statistics keeper, buffered handlers, and buffered senders.

This means:

- Your tasks start when the application starts.
- Your tasks are cancelled when the application shuts down.
- If your task raises an unhandled exception, `asyncio.gather()` will
  propagate it -- the same behaviour as any other Ecosystem internal task.

Write your background tasks to be long-lived. If your task can complete
normally, make sure that is intentional -- a completed task is simply
removed from the gather without affecting the rest of the application.

---

## A note on pre-startup work.

`setup_tasks` is for tasks that need to run *alongside* the application.

If you need to do async work *before* the application starts -- loading a
cache from a database, for example -- do that before `app.start()` using
`asyncio.run()`:

```python
def main():
    asyncio.run(MyCache().load())   # runs before the event loop starts
    with MyServer() as app:
        app.start()                 # event loop starts here
```

`asyncio.run()` creates its own event loop, runs the coroutine to
completion, and exits cleanly. By the time `app.start()` is called, your
cache is already warm.

These two patterns are complementary -- use `asyncio.run()` for one-shot
pre-startup work, and `setup_tasks` for anything that needs to keep running.
