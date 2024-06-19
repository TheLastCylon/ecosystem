from ecosystem import ApplicationBase
from .handlers import GuessANumber, RollDX, RollDXTimes


# --------------------------------------------------------------------------------
class DiceRollerServer(ApplicationBase):
    def __init__(self):
        super().__init__(
            "dice_roller",
            "0",
            "127.0.0.1",
            8888,
            8889,
            [GuessANumber(), RollDX(), RollDXTimes()],
            '/tmp',
        )


# --------------------------------------------------------------------------------
def main():
    app = DiceRollerServer()
    app.start()


# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
