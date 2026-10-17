"""
ProfileMenu Unit for Desktop Environment Manager UI.

Menu screen for managing a specific component profile:
Provides actions to view info, enter, recapture, or delete the profile.
"""

from __future__ import annotations

from typing import Any, Callable

from src.entities.context import AppContext
from src.services import component as component_service
from src.ui.templates import InfoBlock, InfoScreen, MenuOption, MenuScreen
from src.util.time import millis_to_datetime_str


class ProfileMenu(MenuScreen):
    """
    Menu unit for a single profile belonging to a component.

    Options:
        1. Show Info - Displays file path, creation time, and last capture time.
        2. Enter - Activates the profile on the component.
        3. Recapture - Overwrites profile with current component configuration.
        4. Delete - Deletes the profile from disk.
    """

    def __init__(
        self,
        ctx: AppContext,
        component_name: str,
        profile_name: str,
        on_deleted: Callable[[], Any] | None = None,
        can_go_back: bool = True,
        on_back: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.ctx = ctx
        self.component_name = component_name
        self.profile_name = profile_name
        self.on_deleted_callback = on_deleted

        component = ctx.get_component(component_name)
        profiles = component_service.get_profiles(ctx, component_name)
        profile = profiles.get(profile_name)
        display_name = profile.display_name if profile else profile_name

        title = f"{component.DISPLAY_NAME} > {display_name}"
        subtitle = "Profile Management"

        options = [
            MenuOption(
                title="Show Info",
                description="View profile file path, creation time, and last capture time",
                action=self._action_show_info,
            ),
            MenuOption(
                title="Enter",
                description="Apply and activate this profile on the component",
                action=self._action_enter,
            ),
            MenuOption(
                title="Recapture",
                description="Capture current component state into this profile",
                action=self._action_recapture,
            ),
            MenuOption(
                title="Delete",
                description="Permanently delete this profile",
                action=self._action_delete,
            ),
        ]

        super().__init__(
            title=title,
            options=options,
            subtitle=subtitle,
            can_go_back=can_go_back,
            on_back=on_back,
            name=name,
            id=id,
            classes=classes,
        )

    def _get_current_profile(self):
        profiles = component_service.get_profiles(self.ctx, self.component_name)
        return profiles.get(self.profile_name)

    def _action_show_info(self) -> None:
        """Open InfoScreen displaying metadata about the profile."""
        component = self.ctx.get_component(self.component_name)
        profile = self._get_current_profile()
        if not profile:
            self.notify("Profile not found.", title="Error", severity="error")
            return

        file_path = component_service.get_profile_file_path(
            self.ctx, self.component_name, self.profile_name
        )
        created_str = millis_to_datetime_str(profile.creation_timestamp)
        captured_str = millis_to_datetime_str(profile.last_capture_timestamp)

        blocks = [
            InfoBlock(
                title="Profile File Path",
                major=str(file_path),
                minor="Full filesystem path where profile data is saved",
            ),
            InfoBlock(
                title="Creation Time",
                major=created_str,
                minor="Timestamp when this profile was originally created",
            ),
            InfoBlock(
                title="Last Capture Time",
                major=captured_str,
                minor="Timestamp of the most recent profile recapture",
            ),
        ]

        info_screen = InfoScreen(
            title=f"{component.DISPLAY_NAME} > {profile.display_name}",
            subtitle="Profile Metadata & Storage Details",
            blocks=blocks,
            dismiss_button_label="Back to Profile Menu",
        )
        self.app.push_screen(info_screen)

    def _action_enter(self) -> None:
        """Activate this profile on the target component."""
        profile = self._get_current_profile()
        display_name = profile.display_name if profile else self.profile_name

        def task() -> None:
            component_service.set_component_profile(
                self.ctx, self.component_name, self.profile_name
            )

        def on_success(_) -> None:
            self.notify(
                f"Successfully switched to profile '{display_name}'.",
                title="Profile Activated",
                severity="information",
            )

        self.run_with_loading(
            task=task,
            title="Activating Profile",
            status=f"Applying profile '{display_name}'...",
            on_success=on_success,
        )

    def _action_recapture(self) -> None:
        """Recapture component configuration to this profile."""
        profile = self._get_current_profile()
        display_name = profile.display_name if profile else self.profile_name

        def task() -> None:
            component_service.recapture_profile(
                self.ctx, self.component_name, self.profile_name
            )

        def on_success(_) -> None:
            self.notify(
                f"Successfully recaptured profile '{display_name}'.",
                title="Recapture Complete",
                severity="information",
            )

        self.run_with_loading(
            task=task,
            title="Recapturing Profile",
            status=f"Capturing current state into '{display_name}'...",
            on_success=on_success,
        )

    def _action_delete(self) -> None:
        """Delete this profile and dismiss back to parent menu."""
        profile = self._get_current_profile()
        display_name = profile.display_name if profile else self.profile_name

        def task() -> None:
            component_service.delete_profile(
                self.ctx, self.component_name, self.profile_name
            )

        def on_success(_) -> None:
            self.notify(
                f"Profile '{display_name}' deleted.",
                title="Profile Deleted",
                severity="information",
            )
            if self.on_deleted_callback:
                self.on_deleted_callback()
            self.dismiss()

        self.run_with_loading(
            task=task,
            title="Deleting Profile",
            status=f"Removing profile '{display_name}'...",
            on_success=on_success,
        )
