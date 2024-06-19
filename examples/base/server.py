from ecosystem import ApplicationBase, TCPConfig, UDPConfig, UDSConfig


# --------------------------------------------------------------------------------
class BaseServer(ApplicationBase):
    def __init__(self):
        super().__init__(
                "base_example",               # A unique name for your application
                "0",                          # The instance for this application.
                [],                           # Don't worry about this right now, we'll get to it later
                TCPConfig("127.0.0.1", 8888), # The TCP configuration
                UDPConfig("127.0.0.1", 8889), # The UDP configuration
                UDSConfig("/tmp"),            # The UDS configuration
                '/tmp'                        # The directory in which you want log files to be written.
        )


# --------------------------------------------------------------------------------
def main():
    app = BaseServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
