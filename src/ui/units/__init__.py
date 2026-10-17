"""
UI Units for Desktop Environment Manager.

Concrete UI screens composed from UI templates:
    - ComponentMenu: Profile management and creation for a specific component.
    - ComponentsCatalog: List of all registered components.
    - ProfileMenu: Detail actions (info, enter, recapture, delete) for a single profile.
    - EnvironmentMenu: Detail actions (info, enter, delete) for a single environment.
    - EnvironmentsCatalog: List of all stored environments.
    - LoadingScreen: Startup loading display shown during initialization.
"""

from src.ui.units.ComponentMenu import ComponentMenu
from src.ui.units.ComponentsCatalog import ComponentsCatalog
from src.ui.units.EnvironmentMenu import EnvironmentMenu
from src.ui.units.EnvironmentsCatalog import EnvironmentsCatalog
from src.ui.units.LoadingScreen import LoadingScreen
from src.ui.units.ProfileMenu import ProfileMenu

__all__ = [
    "ComponentMenu",
    "ComponentsCatalog",
    "EnvironmentMenu",
    "EnvironmentsCatalog",
    "LoadingScreen",
    "ProfileMenu",
]
