"""
Menu Template for Desktop Environment Manager UI.

A generic menu screen that displays numbered options with descriptions,
supporting keyboard number shortcuts (1-9), arrow navigation, and mouse selection.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, ListItem, ListView

TCSS_PATH = Path(__file__).resolve().parent.parent / "style.tcss"


@dataclass
class MenuOption:
    """
    Data model representing a selectable menu option.

    Attributes:
        title: The display title of the menu item.
        action: The callable function/coroutine to execute when selected.
        description: Optional secondary explanatory text shown below title in gray.
        enabled: Whether the option is active and selectable (defaults to True).
        id: Optional unique identifier for programmatic reference.
    """

    title: str
    action: Callable[[], Any]
    description: str = ""
    enabled: bool = True
    id: str | None = None


class MenuOptionItem(ListItem):
    """Visual widget representing an individual option row inside a ListView."""

    def __init__(self, number: int, option: MenuOption, **kwargs: Any) -> None:
        classes = "menu-item"
        if not option.enabled:
            classes += " menu-item-disabled"
        super().__init__(classes=classes, **kwargs)
        self.number = number
        self.option = option

    def compose(self) -> ComposeResult:
        with Horizontal(classes="menu-item-row"):
            yield Label(f"{self.number}.", classes="menu-item-number")
            with Vertical(classes="menu-item-content"):
                yield Label(self.option.title, classes="menu-item-title")
                if self.option.description:
                    yield Label(
                        self.option.description, classes="menu-item-description"
                    )


class MenuScreen(Screen[None]):
    """
    Generic Menu Screen template.

    Features:
        - Screen title and optional subtitle.
        - Numbered list of options (1, 2, 3...).
        - Direct number key activation (pressing 1 selects option 1).
        - Keyboard arrow / Enter navigation and mouse selection.
        - Configurable back / exit navigation via Escape or callback.
    """

    CSS_PATH = TCSS_PATH

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("q", "go_back", "Quit", show=False),
        Binding("ctrl+q", "app.quit", "Exit", show=True, priority=True),
    ]

    def __init__(
        self,
        title: str,
        options: Sequence[MenuOption] | None = None,
        subtitle: str = "",
        can_go_back: bool = True,
        on_back: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.screen_title = title
        self.subtitle = subtitle
        self.can_go_back = can_go_back
        self.on_back_callback = on_back
        self.options: list[MenuOption] = list(options or [])

    def compose(self) -> ComposeResult:
        with Container(id="menu-screen-container"):
            with Vertical(id="screen-header"):
                yield Label(self.screen_title, id="screen-title")
                if self.subtitle:
                    yield Label(self.subtitle, id="screen-subtitle")

            items = [
                MenuOptionItem(idx + 1, option)
                for idx, option in enumerate(self.options)
            ]
            yield ListView(*items, classes="menu-list", id="menu-list-view")

        yield Footer()

    def on_key(self, event: events.Key) -> None:
        """
        Intercept numeric key presses to trigger corresponding option instantly.
        Supports direct pressing of keys 1 through 9.
        """
        if event.key.isdecimal():
            number = int(event.key)
            if 1 <= number <= len(self.options):
                option_index = number - 1
                option = self.options[option_index]
                if option.enabled:
                    event.prevent_default()
                    event.stop()
                    list_view = self.query_one("#menu-list-view", ListView)
                    list_view.index = option_index
                    self._execute_option(option)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle option selection via Enter key or mouse click."""
        if isinstance(event.item, MenuOptionItem):
            if event.item.option.enabled:
                self._execute_option(event.item.option)

    def set_options(self, options: Sequence[MenuOption]) -> None:
        """Dynamically update the list of menu options and re-render."""
        self.options = list(options)
        if self.is_mounted:
            list_view = self.query_one("#menu-list-view", ListView)
            current_index = list_view.index
            list_view.clear()
            for idx, opt in enumerate(self.options):
                list_view.append(MenuOptionItem(idx + 1, opt))
            if current_index is not None and self.options:
                list_view.index = min(current_index, len(self.options) - 1)

    def _execute_option(self, option: MenuOption) -> None:
        """Execute the chosen option action (supporting sync and async callables)."""
        if not option.enabled:
            return
        result = option.action()
        if inspect.isawaitable(result):
            self.run_worker(result)

    def action_go_back(self) -> None:
        """Action handler for navigating back or exiting."""
        if not self.can_go_back:
            return
        if self.on_back_callback:
            result = self.on_back_callback()
            if inspect.isawaitable(result):
                self.run_worker(result)
        else:
            self.dismiss(None)

    def run_with_loading(
        self,
        task: Callable[[], Any],
        title: str = "Please Wait",
        status: str = "Executing operation...",
        on_success: Callable[[Any], Any] | None = None,
        on_error: Callable[[Exception], Any] | None = None,
    ) -> None:
        """Execute a service task with a LoadingScreen displayed during execution."""
        self.app.run_with_loading(
            task=task,
            title=title,
            status=status,
            on_success=on_success,
            on_error=on_error,
        )


# Convenient alias for intuitive imports
Menu = MenuScreen
