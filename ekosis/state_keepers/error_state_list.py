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

    def has_error_id(self, error_id: str) -> bool:
        error_id_upper = error_id.upper()
        return error_id_upper in self.error_state_map.keys()

    def to_json(self) -> str:
        error_list   : List[ErrorStateKeeper] = self.get_error_states()
        response_list: List[Dict[str, Any]]   = []
        for error in error_list:
            response_list.append(error.to_dict())
        return json.dumps(response_list)

    def increment(self, error_id: str, description: str):
        error_id_upper = error_id.upper()
        if error_id_upper not in self.error_state_map.keys():
            self.error_state_map[error_id_upper] = ErrorStateKeeper(error_id_upper, description)

        self.error_state_map[error_id_upper].increment()

    def clear_some(self, error_id: str, how_many: int):
        error_id_upper = error_id.upper()
        if error_id_upper in self.error_state_map.keys():
            self.error_state_map[error_id_upper].clear_some(how_many)

    def clear_all(self, error_id: str):
        error_id_upper = error_id.upper()
        if error_id_upper in self.error_state_map.keys():
            self.error_state_map[error_id_upper].clear_all()

    def get_error_states(self) -> List[ErrorStateKeeper]:
        result: List[ErrorStateKeeper] = []
        for error_state in self.error_state_map.values():
            if error_state.is_set():
                result.append(error_state)
        return result
