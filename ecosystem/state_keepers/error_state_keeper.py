import json

from ..util import SingletonType


# --------------------------------------------------------------------------------
class ErrorStateKeeper(metaclass=SingletonType):
    def __init__(self, error_id: str, description: str):
        self._error_id   : str = error_id
        self._description: str = description
        self._error_count: int = 0

    def to_dict(self):
        return {
            'error_id'   : self._error_id,
            'description': self._description,
            'count'      : self._error_count
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return f"ErrorState: {self.to_json()}"

    def increment(self):
        self._error_count += 1

    def clear_some(self, how_many: int):
        if self._error_count >= how_many:
            self._error_count = self._error_count - how_many
        else:
            self._error_count = 0

    def clear_all(self):
        self._error_count = 0

    def get_error_count(self):
        return self._error_count

    def is_set(self):
        return self._error_count > 0

    def get_id(self):
        return self._error_id

    def get_description(self):
        return self._description


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
