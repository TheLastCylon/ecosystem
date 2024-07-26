from ekosis.application_base import ApplicationBase

from .endpoints import get_joke # noqa

# --------------------------------------------------------------------------------
class DadJokeServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with DadJokeServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
