"""
ComponentMenu Unit for Desktop Environment Manager UI.

Menu screen for a single component:
Displays all available profiles for the component, allows navigation into ProfileMenu,
and provides a bottom option to create a new profile using InputScreen.
"""

from __future__ import annotations

from typing import Any, Callable

from src.entities.context import AppContext
from src.entities.models import Profile
from src.services import component as component_service
from src.ui.templates import (
    InputScreen,
    MenuOption,
    MenuScreen,
    TextInputField,
)
from src.ui.units.ProfileMenu import ProfileMenu
from src.util.time import millis_to_datetime_str


class ComponentMenu(MenuScreen):
    """
    Menu unit for a single component.

    Displays:
        - Header with component display name.
        - List of available profiles (selecting one opens ProfileMenu).
        - Bottom-most 'Create Profile' option (opens InputScreen).
    """

    def __init__(
        self,
        ctx: AppContext,
        component_name: str,
        can_go_back: bool = True,
        on_back: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.ctx = ctx
        self.component_name = component_name
        self.component = ctx.get_component(component_name)

        super().__init__(
            title=self.component.DISPLAY_NAME,
            options=self._build_options(),
            subtitle="Select a profile to configure, or create a new profile below",
            can_go_back=can_go_back,
            on_back=on_back,
            name=name,
            id=id,
            classes=classes,
        )

    def _build_options(self) -> list[MenuOption]:
        """Construct the list of profile options + the create profile option."""
        profiles = component_service.get_profiles(self.ctx, self.component_name)
        try:
            comp_state = component_service.get_component_state(
                self.ctx, self.component_name
            )
            active_profile = comp_state.active_profile
        except Exception:
            active_profile = None

        options: list[MenuOption] = []

        # List existing profiles
        for profile in profiles.values():
            is_active = active_profile == profile.name
            desc = f"Captured: {millis_to_datetime_str(profile.last_capture_timestamp)}"
            title = profile.display_name
            if is_active:
                desc = f"(Active) {desc}"
                title = f"{title} (Active)"

            # Capture current profile name in closure
            p_name = profile.name
            options.append(
                MenuOption(
                    title=title,
                    description=desc,
                    action=lambda target_name=p_name: self._open_profile_menu(
                        target_name
                    ),
                )
            )

        # Bottom-most option: Create Profile
        options.append(
            MenuOption(
                title="+ Create Profile",
                description="Capture current state and create a new profile",
                action=self._open_create_profile_screen,
            )
        )

        return options

    def refresh_profiles(self) -> None:
        """Reload profiles from backend and update menu options."""
        self.set_options(self._build_options())

    def on_screen_resume(self) -> None:
        """Refresh profiles when returning to this menu."""
        self.refresh_profiles()

    def _open_profile_menu(self, profile_name: str) -> None:
        """Open the ProfileMenu for the selected profile."""
        profile_menu = ProfileMenu(
            ctx=self.ctx,
            component_name=self.component_name,
            profile_name=profile_name,
            on_deleted=self.refresh_profiles,
        )
        self.app.push_screen(profile_menu)

    def _open_create_profile_screen(self) -> None:
        """Open an InputScreen to create a new profile."""
        fields = [
            TextInputField(
                key="display_name",
                label="Profile Name",
                description="Enter the display name for this new profile",
                placeholder="e.g. Work-Setup",
                required=True,
            )
        ]

        def on_submit(values: dict[str, Any]) -> None:
            display_name = values["display_name"].strip()
            # Use the profile model's display name factory to create the object
            new_profile = Profile.create_from_display_name(display_name)

            def task() -> None:
                component_service.create_profile(
                    self.ctx, self.component_name, new_profile
                )

            def on_success(_) -> None:
                self.notify(
                    f"Profile '{display_name}' created successfully.",
                    title="Profile Created",
                    severity="information",
                )
                self.refresh_profiles()

            self.run_with_loading(
                task=task,
                title="Creating Profile",
                status=f"Capturing current state into '{display_name}'...",
                on_success=on_success,
            )

        input_screen = InputScreen(
            title=f"{self.component.DISPLAY_NAME} > Create Profile",
            subtitle="Provide a name to capture the current state as a new profile",
            fields=fields,
            submit_label="Create",
            cancel_label="Cancel",
            on_submit=on_submit,
        )
        self.app.push_screen(input_screen)
