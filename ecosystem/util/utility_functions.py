import uuid
import asyncio


# --------------------------------------------------------------------------------
def camel_to_snake(input_string: str) -> str:
    output_string = ""
    for i in range(len(input_string)):
        if input_string[i].isupper() and i != 0:
            output_string += "_" + input_string[i].lower()
        else:
            output_string += input_string[i].lower()
    return output_string


# --------------------------------------------------------------------------------
def string_to_uuid(value: str) -> uuid.UUID | bool:
    try:
        return uuid.UUID(value)
    except ValueError:
        return False


# --------------------------------------------------------------------------------
def run_soon(function):
    def called_task(loop, *args, **kwargs):
        loop.create_task(function(*args, **kwargs))

    def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        loop.call_soon(called_task, loop, *args, **kwargs)
    return wrapper
