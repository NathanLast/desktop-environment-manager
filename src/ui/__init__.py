"""
Desktop Environment Manager UI Package.

Provides generic templates and concrete UI units built using Textual.
Styles are centrally governed by style.tcss.
"""

from pathlib import Path

from src.ui.templates import (
    DropdownInputField,
    InfoBlock,
    InfoScreen,
    InputField,
    InputScreen,
    IntegerInputField,
    Menu,
    MenuOption,
    MenuScreen,
    TextInputField,
    ToggleInputField,
)
from src.ui.units import (
    ComponentMenu,
    ComponentsCatalog,
    EnvironmentMenu,
    EnvironmentsCatalog,
    ProfileMenu,
)
from src.ui.app import AutomationApp, run_app

TCSS_PATH = Path(__file__).resolve().parent / "style.tcss"

__all__ = [
    "TCSS_PATH",
    "AutomationApp",
    "run_app",
    # Templates
    "InfoScreen",
    "InfoBlock",
    "MenuScreen",
    "Menu",
    "MenuOption",
    "InputScreen",
    "InputField",
    "TextInputField",
    "DropdownInputField",
    "ToggleInputField",
    "IntegerInputField",
    # Units
    "ComponentMenu",
    "ComponentsCatalog",
    "EnvironmentMenu",
    "EnvironmentsCatalog",
    "ProfileMenu",
]
