from ekosis.application_base import ApplicationBase

from .endpoints import ( # noqa
    test_endpoint,
    test_pass_through,
    test_queued_pass_through
)

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
