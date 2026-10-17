from __future__ import annotations

from typing import Optional, Iterable, TYPE_CHECKING
from pathlib import Path

from src.storage.storage_handler import StorageHandler
from src.storage.state_handler import StateHandler
from src.entities.models import Profile, AppState

if TYPE_CHECKING:
    from src.entities.component import Component


class AppContext:
    def __init__(
        self,
        data_dir: Path,
        components: list["Component"],
        active_environment: Optional[str],
    ):
        self._active_env: Optional[str] = active_environment
        self._components: dict[str, "Component"] = {
            component.NAME: component for component in components
        }
        self._data_dir = StorageHandler(data_dir)

    @property
    def environment(self) -> Optional[str]:
        return self._active_env

    @environment.setter
    def environment(self, new_env: Optional[str]) -> None:
        self._active_env = new_env
        with StateHandler[AppState](self._data_dir.sub_handler("app")) as app_state:
            app_state.active_environment = new_env

    def get_component(self, name: str) -> "Component":
        return self._components[name]

    @property
    def data_dir(self) -> StorageHandler:
        return self._data_dir

    @property
    def components(self) -> Iterable["Component"]:
        return self._components.values()


class ComponentContext:
    def __init__(
        self,
        component: Component,
        component_storage: StorageHandler,
        profiles_storage: StorageHandler,
    ):
        self._component = component
        self._component_storage = component_storage
        self._profiles_storage = profiles_storage

        component_storage.assert_directory_exists()
        profiles_storage.assert_directory_exists()

    def profile_file_path(self, profile: Profile) -> Path:
        extension = self._component.EXTENSION
        extension = f".{extension}" if extension is not None else ""
        profile_file_rel_path = f"{profile.name}/data{extension}"
        return self._profiles_storage.get_full_path(rel_path=profile_file_rel_path)

    def profile_dir_path(self, profile: Profile) -> Path:
        return self._profiles_storage.get_full_path(profile.name)

    def storage(self) -> StorageHandler:
        return self._component_storage
