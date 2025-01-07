from ekosis.application_base import ApplicationBase
from ekosis.middleware.manager import MiddlewareManager

from .endpoints import (app_a_endpoint, app_a_queued_pass_through, app_a_pass_through, app_a_queued_sender)
from .middleware import MiddlewareTest

middleware_manager = MiddlewareManager()

middleware_manager.add(MiddlewareTest())

# --------------------------------------------------------------------------------
class TestAppAServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with TestAppAServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
