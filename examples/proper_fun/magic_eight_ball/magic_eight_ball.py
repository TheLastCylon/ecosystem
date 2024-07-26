from ekosis.application_base import ApplicationBase

from .endpoints import get_prediction # noqa

# --------------------------------------------------------------------------------
class Magic8Ball(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with Magic8Ball() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
