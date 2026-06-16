from ekosis.application_base  import ApplicationBase
from ekosis_otlp_traces.setup import initiate_otlp_tracing

from .endpoints import pick_numbers_endpoint # noqa

# --------------------------------------------------------------------------------
class NumberPickerServer(ApplicationBase):
    def __init__(self):
        super().__init__()
        initiate_otlp_tracing()

# --------------------------------------------------------------------------------
def main():
    with NumberPickerServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
