# --------------------------------------------------------------------------------
class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


# --------------------------------------------------------------------------------
class SingletonBase(metaclass=SingletonType):
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
