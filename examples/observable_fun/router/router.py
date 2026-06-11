from ekosis.application_base  import ApplicationBase
from ekosis_jaeger_http.setup import initiate_jaeger_tracing

from .endpoints import process_message # noqa

# --------------------------------------------------------------------------------
class RouterServer(ApplicationBase):
    def __init__(self):
        super().__init__()
        initiate_jaeger_tracing()

# --------------------------------------------------------------------------------
def main():
    with RouterServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
