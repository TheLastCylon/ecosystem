from ekosis.application_base import ApplicationBase

from .endpoints import test_endpoint # noqa

# --------------------------------------------------------------------------------
class TestAppBServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with TestAppBServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
