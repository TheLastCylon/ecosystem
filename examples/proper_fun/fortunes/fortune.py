from ekosis.application_base import ApplicationBase

from .endpoints import get_fortune # noqa

# --------------------------------------------------------------------------------
class FortuneServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with FortuneServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
