from dataclasses import dataclass, field
from typing import Optional

from src.util.model import Model
from src.util.string import to_var_name
from src.util.time import get_now_millis


@dataclass
class Profile(Model):
    name: str
    display_name: str
    creation_timestamp: int
    last_capture_timestamp: int
    # num static environments using this profile
    environment_usage_count: int = 0

    @classmethod
    def create_from_display_name(cls, display_name: str) -> "Profile":
        now_millis = get_now_millis()
        return cls(
            name=to_var_name(display_name),
            display_name=display_name,
            creation_timestamp=now_millis,
            last_capture_timestamp=now_millis,
        )


@dataclass
class ComponentState(Model):
    setup: bool = False
    active_profile: Optional[str] = None
    env_locked: bool = False


@dataclass
class AppState(Model):
    active_environment: Optional[str] = None


@dataclass
class Environment(Model):
    name: str
    display_name: str
    creation_timestamp: int
    dynamic: bool = field(default=False)
    bound_components: list[str] = field(default_factory=list)
    # if static (not dynamic), map each bound component to the profile the
    # environment should use
    profile_mapping: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create_from_display_name(
        cls,
        display_name: str,
        dynamic: bool = False,
        bound_components: list[str] = None,
        profile_mapping: dict[str, str] = None,
    ) -> "Environment":
        if bound_components is None:
            bound_components = []
        if profile_mapping is None:
            profile_mapping = {}

        return Environment(
            name=to_var_name(display_name),
            display_name=display_name,
            creation_timestamp=get_now_millis(),
            dynamic=dynamic,
            bound_components=bound_components,
            profile_mapping=profile_mapping,
        )
