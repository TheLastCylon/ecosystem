from ekosis.application_base import ApplicationBase

from .endpoints import process_message # noqa

# --------------------------------------------------------------------------------
class RouterServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with RouterServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
