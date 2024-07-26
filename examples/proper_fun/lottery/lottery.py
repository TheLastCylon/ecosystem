from ekosis.application_base import ApplicationBase

from .endpoints import pick_numbers_endpoint # noqa

# --------------------------------------------------------------------------------
class NumberPickerServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with NumberPickerServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
