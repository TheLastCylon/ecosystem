import asyncio

FIRE_AND_FORGET_TASKS = set()

# --------------------------------------------------------------------------------
def fire_and_forget_task_for_loop(loop: asyncio.AbstractEventLoop, coroutine):
    global FIRE_AND_FORGET_TASKS
    task = loop.create_task(coroutine)
    FIRE_AND_FORGET_TASKS.add(task)
    task.add_done_callback(FIRE_AND_FORGET_TASKS.discard)
    return task

# --------------------------------------------------------------------------------
def fire_and_forget_task(coroutine):
    global FIRE_AND_FORGET_TASKS
    task = asyncio.create_task(coroutine)
    FIRE_AND_FORGET_TASKS.add(task)
    # Should this rather be:
    # task.add_done_callback(lambda x: FIRE_AND_FORGET_TASKS.discard(x))
    task.add_done_callback(FIRE_AND_FORGET_TASKS.discard)
    return task

# --------------------------------------------------------------------------------
def run_soon(function):
    def called_task(loop: asyncio.AbstractEventLoop, *args, **kwargs):
        task = loop.create_task(function(*args, **kwargs))
        FIRE_AND_FORGET_TASKS.add(task)
        task.add_done_callback(FIRE_AND_FORGET_TASKS.discard)
        return task

    def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        loop.call_soon(called_task, loop, *args, **kwargs)
    return wrapper
