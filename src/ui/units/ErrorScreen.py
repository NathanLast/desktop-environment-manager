"""
ErrorScreen Unit for Desktop Environment Manager UI.

Dedicated screen displayed when an initialization error occurs before the program starts.
Presents the error message and provides only an exit action.
"""

from __future__ import annotations

from pathlib import Path

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Label

TCSS_PATH = Path(__file__).resolve().parent.parent / "style.tcss"


class ErrorScreen(Screen[None]):
    """
    Error screen unit for fatal or initialization errors.

    Displays:
        - Error header with warning/failure title.
        - Scrollable area presenting the error message.
        - Exit button and keyboard bindings (Ctrl+Q, Esc, Enter) to quit.
    """

    CSS_PATH = TCSS_PATH

    BINDINGS = [
        Binding("escape", "exit_app", "Exit", show=True, priority=True),
        Binding("ctrl+q", "exit_app", "Exit", show=True, priority=True),
        Binding("enter", "exit_app", "Exit", show=False, priority=True),
        Binding("q", "exit_app", "Exit", show=False, priority=True),
    ]

    def __init__(
        self,
        error_message: str,
        title: str = "Initialization Error",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.error_message = error_message
        self.screen_title = title

    def compose(self) -> ComposeResult:
        with Container(id="error-screen-container"):
            with Vertical(id="error-header"):
                yield Label(
                    f"[bold]{escape(self.screen_title)}[/bold]", id="error-title"
                )

            with VerticalScroll(id="error-message-container"):
                yield Label(escape(self.error_message), id="error-message-text")

            with Vertical(id="error-footer-container"):
                yield Button("Exit Program", id="exit-btn", classes="btn-error")

        yield Footer()

    def action_exit_app(self) -> None:
        """Exit the entire application."""
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Exit button press."""
        if event.button.id == "exit-btn":
            self.action_exit_app()
