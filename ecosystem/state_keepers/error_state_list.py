import json
from typing import Dict, List, Any

from .error_state_keeper import ErrorStateKeeper

from ..util.singleton import SingletonType


# --------------------------------------------------------------------------------
class ErrorStateList(metaclass=SingletonType):
    error_state_map: Dict[str, ErrorStateKeeper] = {}

    def __init__(self):
        pass

    def __str__(self) -> str:
        return self.to_json()

    def to_json(self) -> str:
        error_list   : List[ErrorStateKeeper]     = self.get_error_states()
        response_list: List[Dict[str, Any]] = []
        for error in error_list:
            response_list.append(error.to_dict())
        return json.dumps(response_list)

    def increment(self, error_id: str, description: str):
        error_id = error_id.upper()
        if error_id not in self.error_state_map.keys():
            self.error_state_map[error_id] = ErrorStateKeeper(error_id, description)

        self.error_state_map[error_id].increment()

    def clear_some(self, error_id: str, how_many: int):
        if error_id in self.error_state_map.keys():
            self.error_state_map[error_id].clear_some(how_many)

    def clear_all(self, error_id: str):
        if error_id in self.error_state_map.keys():
            self.error_state_map[error_id].clear_all()

    def get_error_states(self) -> List[ErrorStateKeeper]:
        result: List[ErrorStateKeeper] = []
        for error_state in self.error_state_map.values():
            if error_state.is_set():
                result.append(error_state)
        return result


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    print("Not an executable script, intended for use in other scripts")
