from typing import Protocol
from abc import abstractmethod
from typing import Optional, TypeAlias, ClassVar

from src.util.string import is_valid_var_name
from src.entities.models import Profile
from src.entities.context import ComponentContext


SuccessStatus: TypeAlias = Optional[int]


class Component(Protocol):
    __SUB_CLASSES: ClassVar[dict[str, type["Component"]]] = {}
    NAME: ClassVar[str]
    DISPLAY_NAME: ClassVar[str]
    EXTENSION: ClassVar[Optional[str]] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "NAME" not in cls.__dict__:
            raise Exception(
                f"Component class '{cls.__name__}' must explicitly set a NAME class attribute"
            )
        if not is_valid_var_name(cls.NAME):
            raise Exception(
                f"Component class '{cls.__name__}' must set a valid NAME attribute"
            )
        if cls.NAME in cls.__SUB_CLASSES:
            raise Exception(
                f"Component class '{cls.__name__}' must set a unique NAME "
                f"attribute: component with the name '{cls.NAME}' already exists"
            )
        cls.__SUB_CLASSES[cls.NAME] = cls

        if not hasattr(cls, "DISPLAY_NAME"):
            cls.DISPLAY_NAME = cls.NAME  # use name as default display name

    @abstractmethod
    def enter_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        """set the component configuration to the received profile"""

    @abstractmethod
    def exit_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        """unset the component configuration from the received profile.
        where applicable, skipping (leaving the component as-is) is accepted"""

    @abstractmethod
    def capture_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        """capture the current configuration of the component to the profile file.
        might be used with existing profile files (recaptures)"""

    def setup(self, ctx: ComponentContext) -> SuccessStatus:
        """set up the component. runs the first time the app starts with this
        component configured (runs only one time). implementation is optional
        (default behaviour does nothing)"""
        return None

    def init(self, ctx: ComponentContext) -> SuccessStatus:
        """initialize the component. runs each time the app starts. implementation
        is optional (default behvaiour does nothing)"""
        return None
