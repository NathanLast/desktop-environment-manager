"""
EnvironmentMenu Unit for Desktop Environment Manager UI.

Menu screen for managing an individual Environment:
Provides actions to show environment info, enter (activate) it, or delete it.
"""

from __future__ import annotations

from typing import Any, Callable

from textual.widgets import Label

from src.entities.context import AppContext
from src.services import environment as environment_service
from src.ui.templates import InfoBlock, InfoScreen, MenuOption, MenuScreen
from src.util.time import millis_to_datetime_str


class EnvironmentMenu(MenuScreen):
    """
    Menu unit for a single environment.

    Options:
        1. Show Info - Displays creation time, bound components, and profile mappings.
        2. Enter / Exit - Activates or exits (auto-recaptures dynamic state) the environment.
        3. Delete - Deletes the environment and decreases profile usage counts.
    """

    def __init__(
        self,
        ctx: AppContext,
        environment_name: str,
        on_deleted: Callable[[], Any] | None = None,
        can_go_back: bool = True,
        on_back: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.ctx = ctx
        self.environment_name = environment_name
        self.on_deleted_callback = on_deleted

        env = self._get_environment()
        display_name = env.display_name if env else environment_name
        is_active = self.ctx.environment == self.environment_name
        subtitle = (
            "(Active) Environment Configuration & Management"
            if is_active
            else "Environment Configuration & Management"
        )

        super().__init__(
            title=display_name,
            options=self._build_options(),
            subtitle=subtitle,
            can_go_back=can_go_back,
            on_back=on_back,
            name=name,
            id=id,
            classes=classes,
        )

    def _build_options(self) -> list[MenuOption]:
        """Construct menu options dynamically depending on whether environment is active."""
        is_active = self.ctx.environment == self.environment_name
        options = [
            MenuOption(
                title="Show Info",
                description="View creation time, bound components, and profile mappings",
                action=self._action_show_info,
            ),
        ]

        if is_active:
            options.append(
                MenuOption(
                    title="Exit",
                    description="Deactivate environment, auto-recapturing changes and unlocking components",
                    action=self._action_exit,
                )
            )
        else:
            options.append(
                MenuOption(
                    title="Enter",
                    description="Activate this environment across all bound components",
                    action=self._action_enter,
                )
            )

        options.append(
            MenuOption(
                title="Delete",
                description="Permanently remove this environment",
                action=self._action_delete,
            )
        )
        return options

    def refresh_menu(self) -> None:
        """Update options and subtitle when active status changes."""
        self.set_options(self._build_options())
        if self.is_mounted:
            is_active = self.ctx.environment == self.environment_name
            try:
                subtitle_label = self.query_one("#screen-subtitle", Label)
                subtitle_label.update(
                    "(Active) Environment Configuration & Management"
                    if is_active
                    else "Environment Configuration & Management"
                )
            except Exception:
                pass

    def on_screen_resume(self) -> None:
        """Refresh options when returning to this menu."""
        self.refresh_menu()

    def _get_environment(self):
        envs = environment_service.get_environments(self.ctx)
        return envs.get(self.environment_name)

    def _action_show_info(self) -> None:
        """Open InfoScreen displaying metadata and component mappings for this environment."""
        env = self._get_environment()
        if not env:
            self.notify("Environment not found.", title="Error", severity="error")
            return

        created_str = millis_to_datetime_str(env.creation_timestamp)
        type_str = "Dynamic" if env.dynamic else "Static"
        type_desc = (
            "Preserves changes made to component configurations by auto-recapturing their profiles upon exit"
            if env.dynamic
            else "Applies fixed, predefined component profiles upon activation"
        )

        blocks: list[InfoBlock] = [
            InfoBlock(
                title="Creation Time",
                major=created_str,
                minor="Timestamp when this environment was configured",
            ),
            InfoBlock(
                title="Environment Type",
                major=type_str,
                minor=type_desc,
            ),
            InfoBlock(
                title="Bound Components",
                major=", ".join(env.bound_components)
                if env.bound_components
                else "None",
                minor=f"Total bound components: {len(env.bound_components)}",
            ),
        ]

        # If static, display selected profile per bound component
        if not env.dynamic and env.profile_mapping:
            for comp_name in env.bound_components:
                selected_profile = env.profile_mapping.get(comp_name, "None")
                blocks.append(
                    InfoBlock(
                        title=f"Bound Component > {comp_name}",
                        major=f"Profile: {selected_profile}",
                        minor="Assigned profile applied when entering this environment",
                    )
                )

        info_screen = InfoScreen(
            title=env.display_name,
            subtitle="Environment Information & Profile Mappings",
            blocks=blocks,
            dismiss_button_label="Back to Environment Menu",
        )
        self.app.push_screen(info_screen)

    def _action_enter(self) -> None:
        """Activate this environment."""
        env = self._get_environment()
        display_name = env.display_name if env else self.environment_name

        def task() -> None:
            environment_service.enter_environment(self.ctx, self.environment_name)

        def on_success(_) -> None:
            self.notify(
                f"Successfully entered environment '{display_name}'.",
                title="Environment Activated",
                severity="information",
            )
            self.refresh_menu()

        self.run_with_loading(
            task=task,
            title="Activating Environment",
            status=f"Applying environment '{display_name}' across bound components...",
            on_success=on_success,
        )

    def _action_exit(self) -> None:
        """Deactivate this environment, auto-recapturing dynamic component changes."""
        env = self._get_environment()
        display_name = env.display_name if env else self.environment_name

        def task() -> None:
            environment_service.exit_cur_environment(self.ctx)

        def on_success(_) -> None:
            self.notify(
                f"Successfully exited environment '{display_name}'.",
                title="Environment Deactivated",
                severity="information",
            )
            self.refresh_menu()

        self.run_with_loading(
            task=task,
            title="Exiting Environment",
            status=f"Auto-recapturing state and exiting '{display_name}'...",
            on_success=on_success,
        )

    def _action_delete(self) -> None:
        """Delete this environment and return to previous menu."""
        env = self._get_environment()
        display_name = env.display_name if env else self.environment_name

        def task() -> None:
            environment_service.delete_environment(self.ctx, self.environment_name)

        def on_success(_) -> None:
            self.notify(
                f"Environment '{display_name}' deleted.",
                title="Environment Deleted",
                severity="information",
            )
            if self.on_deleted_callback:
                self.on_deleted_callback()
            self.dismiss()

        self.run_with_loading(
            task=task,
            title="Deleting Environment",
            status=f"Removing environment '{display_name}'...",
            on_success=on_success,
        )
