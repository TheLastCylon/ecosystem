from ekosis.application_base  import ApplicationBase
from ekosis_otlp_traces.setup import initiate_otlp_tracing

from .endpoints import get_prediction # noqa

# --------------------------------------------------------------------------------
class Magic8Ball(ApplicationBase):
    def __init__(self):
        super().__init__()
        initiate_otlp_tracing()

# --------------------------------------------------------------------------------
def main():
    with Magic8Ball() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
