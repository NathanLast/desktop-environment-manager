import json
from typing import Optional
from pathlib import Path

from src.util.model import ModelParameterizedClass, GenericModelType
from src.storage.storage_handler import StorageHandler

_STATE_FILE_NAME = Path("__state__.json")


class StateHandler(ModelParameterizedClass[GenericModelType]):
    _OPEN_STATES: set[str] = set()

    def __init__(self, obj_path: Path | StorageHandler):
        super().__init__()

        if isinstance(obj_path, Path):
            obj_path = StorageHandler(obj_path)

        self._state_file_path = obj_path.get_full_path(_STATE_FILE_NAME)
        self._path = obj_path
        self._open_state: Optional[GenericModelType] = None

    def has_state(self) -> bool:
        return self._state_file_path.exists()

    def get_state(self) -> GenericModelType:
        return self.model_class.from_dict(self._load())

    def set_state(self, state: GenericModelType) -> None:
        self._dump(state.to_dict())

    def __enter__(self) -> GenericModelType:
        state_file_path = str(self._state_file_path)
        if state_file_path in self._OPEN_STATES:
            raise RuntimeError(
                f"cannot open state '{state_file_path}': state already open"
            )
        self._OPEN_STATES.add(state_file_path)
        self._open_state = self.get_state()
        return self._open_state

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.set_state(self._open_state)
        self._open_state = None
        self._OPEN_STATES.remove(str(self._state_file_path))

    def _load(self) -> dict:
        self._path.assert_file_exists(_STATE_FILE_NAME)
        return json.loads(self._state_file_path.read_text() or "{}")

    def _dump(self, obj: dict) -> None:
        self._state_file_path.write_text(json.dumps(obj, indent=4))
