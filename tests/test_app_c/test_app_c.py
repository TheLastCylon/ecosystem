import asyncio

from ekosis.application_base import ApplicationBase

from .endpoints import app_c_setup_task_ran # noqa
import tests.test_app_c.endpoints as app_c_endpoints

# --------------------------------------------------------------------------------
async def background_task():
    app_c_endpoints.setup_task_ran = True
    while True:
        await asyncio.sleep(1)

# --------------------------------------------------------------------------------
class TestAppCServer(ApplicationBase):
    def __init__(self):
        super().__init__()

    async def setup_tasks(self, tasks: list):
        tasks.append(asyncio.create_task(background_task()))

# --------------------------------------------------------------------------------
def main():
    with TestAppCServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
