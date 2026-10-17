"""
ComponentsCatalog Unit for Desktop Environment Manager UI.

Catalog screen displaying all available components registered in AppContext.
Selecting a component opens its ComponentMenu.
"""

from __future__ import annotations

from typing import Any, Callable

from src.entities.context import AppContext
from src.services import component as component_service
from src.ui.templates import MenuOption, MenuScreen
from src.ui.units.ComponentMenu import ComponentMenu


class ComponentsCatalog(MenuScreen):
    """
    Menu unit listing all registered components.

    Selecting any component transitions to that component's ComponentMenu.
    """

    def __init__(
        self,
        ctx: AppContext,
        can_go_back: bool = True,
        on_back: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.ctx = ctx

        super().__init__(
            title="Components Catalog",
            options=self._build_options(),
            subtitle="Select a component to manage its profiles and settings",
            can_go_back=can_go_back,
            on_back=on_back,
            name=name,
            id=id,
            classes=classes,
        )

    def _build_options(self) -> list[MenuOption]:
        """Build menu options from registered components in AppContext."""
        components = list(self.ctx._components.values())
        if not components:
            return [
                MenuOption(
                    title="No Components Available",
                    description="No system components are registered in AppContext",
                    action=lambda: None,
                    enabled=False,
                )
            ]

        options: list[MenuOption] = []
        for component in components:
            c_name = component.NAME
            profiles_count = len(component_service.get_profiles(self.ctx, c_name))
            desc = f"Identifier: {c_name} | Saved Profiles: {profiles_count}"

            options.append(
                MenuOption(
                    title=component.DISPLAY_NAME,
                    description=desc,
                    action=lambda target_name=c_name: self._open_component_menu(
                        target_name
                    ),
                )
            )

        return options

    def refresh_components(self) -> None:
        """Reload components and saved profile counts from backend and update menu options."""
        self.set_options(self._build_options())

    def on_screen_resume(self) -> None:
        """Refresh component options and profile counts when returning to this screen."""
        self.refresh_components()

    def _open_component_menu(self, component_name: str) -> None:
        """Navigate to the ComponentMenu for the chosen component."""
        component_menu = ComponentMenu(ctx=self.ctx, component_name=component_name)
        self.app.push_screen(component_menu)
