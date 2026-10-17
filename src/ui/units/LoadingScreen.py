"""
LoadingScreen Unit for Desktop Environment Manager UI.

Screen shown while the application executes its startup initialization function.
Presents a loading spinner and status feedback, keeping the UI visible and responsive.
"""

from __future__ import annotations

from pathlib import Path

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, LoadingIndicator

TCSS_PATH = Path(__file__).resolve().parent.parent / "style.tcss"


class LoadingScreen(Screen[None]):
    """
    Loading screen unit displayed during startup initialization.

    Features:
        - Animated loading indicator.
        - Informative title and status label.
        - Ctrl+Q binding to cancel/exit.
    """

    CSS_PATH = TCSS_PATH

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Exit", show=True, priority=True),
    ]

    def __init__(
        self,
        title: str = "Starting Desktop Environment Manager",
        status: str = "Initializing system components and configurations...",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.loading_title = title
        self.loading_status = status

    def compose(self) -> ComposeResult:
        with Container(id="loading-screen-container"):
            with Vertical():
                yield Label(
                    f"[bold]{escape(self.loading_title)}[/bold]", id="loading-title"
                )
                yield Label(escape(self.loading_status), id="loading-status")
                yield LoadingIndicator(id="loading-spinner")

        yield Footer()

    def update_status(self, new_status: str) -> None:
        """Dynamically update the status label."""
        self.loading_status = new_status
        if self.is_mounted:
            label = self.query_one("#loading-status", Label)
            label.update(escape(new_status))
