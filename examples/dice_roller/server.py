from ecosystem import ApplicationBase, TCPConfig, UDPConfig, UDSConfig
from .handlers import GuessANumber, RollDX, RollDXTimes


# --------------------------------------------------------------------------------
class DiceRollerServer(ApplicationBase):
    def __init__(self):
        super().__init__(
            "dice_roller",
            "0",
            [GuessANumber(), RollDX(), RollDXTimes()],
            TCPConfig("127.0.0.1", 8888),
            UDPConfig("127.0.0.1", 8889),
            UDSConfig("/tmp"),
            '/tmp'
        )


# --------------------------------------------------------------------------------
def main():
    app = DiceRollerServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
