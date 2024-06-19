# --------------------------------------------------------------------------------
class TCPUDPConfigBase:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port


# --------------------------------------------------------------------------------
class TCPConfig(TCPUDPConfigBase):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)


# --------------------------------------------------------------------------------
class UDPConfig(TCPUDPConfigBase):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)


# --------------------------------------------------------------------------------
class UDSConfig:
    def __init__(self, directory: str, socket_file_name: str = "use_default"):
        self.directory       : str = directory
        self.socket_file_name: str = socket_file_name
