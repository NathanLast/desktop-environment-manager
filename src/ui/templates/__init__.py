"""
UI Templates for Desktop Environment Manager.

This package provides generic, reusable Textual UI screen templates:
    - InfoScreen: Structured information presentation with InfoBlock items.
    - MenuScreen / Menu: Numbered interactive menu with keyboard shortcuts.
    - InputScreen: Form input gathering using modular InputField components.
"""

from src.ui.templates.InfoScreen import InfoBlock, InfoBlockWidget, InfoScreen
from src.ui.templates.InputScreen import (
    DropdownInputField,
    DropdownInputMethod,
    InputField,
    InputFieldContainer,
    InputMethod,
    InputScreen,
    IntegerInputField,
    IntegerInputMethod,
    MultiSelectInputField,
    MultiSelectInputMethod,
    SelectInputField,
    SwitchInputField,
    TextAreaInputField,
    TextAreaInputMethod,
    TextInputField,
    TextInputMethod,
    ToggleInputField,
    ToggleInputMethod,
)
from src.ui.templates.Menu import Menu, MenuOption, MenuOptionItem, MenuScreen

__all__ = [
    # InfoScreen components
    "InfoBlock",
    "InfoBlockWidget",
    "InfoScreen",
    # Menu components
    "Menu",
    "MenuOption",
    "MenuOptionItem",
    "MenuScreen",
    # InputScreen components
    "InputField",
    "InputMethod",
    "InputFieldContainer",
    "InputScreen",
    "TextInputField",
    "TextInputMethod",
    "DropdownInputField",
    "DropdownInputMethod",
    "SelectInputField",
    "ToggleInputField",
    "ToggleInputMethod",
    "SwitchInputField",
    "IntegerInputField",
    "IntegerInputMethod",
    "TextAreaInputField",
    "TextAreaInputMethod",
    "MultiSelectInputField",
    "MultiSelectInputMethod",
]
