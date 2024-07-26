from ..datagram_client_base import DatagramClientBase

# --------------------------------------------------------------------------------
class UDPClient(DatagramClientBase):
    def __init__(
        self,
        server_host: str,
        server_port: int,
        timeout    : int   = 5,
        max_retries: int   = 3,
        retry_delay: float = 0.1,
    ):
        super().__init__(server_host, server_port, timeout, max_retries, retry_delay)

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
