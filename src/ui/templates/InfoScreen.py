"""
InfoScreen Template for Desktop Environment Manager UI.

A generic screen template that presents structured information to the user
via vertically stacked InfoBlock components.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Callable, Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Label

TCSS_PATH = Path(__file__).resolve().parent.parent / "style.tcss"


@dataclass(frozen=True)
class InfoBlock:
    """
    Data model representing a single block of information.

    Attributes:
        title: Bold title of the information category/field.
        major: Primary information text displayed inline with title.
        minor: Optional secondary text displayed below in muted/gray style.
    """

    title: str
    major: str
    minor: str = ""


class InfoBlockWidget(Widget):
    """Widget rendering an individual InfoBlock in standard format."""

    def __init__(self, block: InfoBlock, **kwargs: Any) -> None:
        super().__init__(classes="info-block", **kwargs)
        self.block = block

    def compose(self) -> ComposeResult:
        headline = (
            f"[bold]{escape(self.block.title)}:[/bold] {escape(self.block.major)}"
        )
        yield Label(headline, classes="info-block-headline")
        if self.block.minor:
            yield Label(escape(self.block.minor), classes="info-block-minor")


class InfoScreen(Screen[None]):
    """
    Generic Screen template for displaying lists of informational blocks.

    Displays:
        - Screen title and optional subtitle at the top.
        - Scrollable list of InfoBlocks formatted vertically.
        - Dismiss/Back action button and keyboard navigation.
    """

    CSS_PATH = TCSS_PATH

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Quit", show=False),
        Binding("enter", "dismiss_screen", "Done", show=False),
        Binding("ctrl+q", "app.quit", "Exit", show=True, priority=True),
    ]

    def __init__(
        self,
        title: str,
        blocks: Sequence[InfoBlock] | None = None,
        subtitle: str = "",
        can_dismiss: bool = True,
        dismiss_button_label: str = "Back",
        on_dismiss: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.screen_title = title
        self.subtitle = subtitle
        self.can_dismiss = can_dismiss
        self.dismiss_button_label = dismiss_button_label
        self.on_dismiss_callback = on_dismiss
        self._initial_blocks = list(blocks or [])

    def compose(self) -> ComposeResult:
        with Container(id="info-screen-container"):
            with Vertical(id="screen-header"):
                yield Label(self.screen_title, id="screen-title")
                if self.subtitle:
                    yield Label(self.subtitle, id="screen-subtitle")

            with VerticalScroll(id="info-scroll-container"):
                for block in self._initial_blocks:
                    yield InfoBlockWidget(block)

            if self.can_dismiss:
                with Horizontal(id="screen-footer-container"):
                    yield Button(
                        self.dismiss_button_label,
                        id="back-button",
                        classes="btn-primary",
                    )
        yield Footer()

    def add_block(self, block: InfoBlock) -> None:
        """Add a single InfoBlock dynamically to the screen."""
        scroll_container = self.query_one("#info-scroll-container", VerticalScroll)
        scroll_container.mount(InfoBlockWidget(block))

    def set_blocks(self, blocks: Sequence[InfoBlock]) -> None:
        """Replace all current InfoBlocks with a new list."""
        scroll_container = self.query_one("#info-scroll-container", VerticalScroll)
        scroll_container.remove_children()
        for block in blocks:
            scroll_container.mount(InfoBlockWidget(block))

    def action_dismiss_screen(self) -> None:
        """Action handler for dismissing the screen."""
        if not self.can_dismiss:
            return
        if self.on_dismiss_callback:
            self.on_dismiss_callback()
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle click on the dismiss button."""
        if event.button.id == "back-button":
            self.action_dismiss_screen()
