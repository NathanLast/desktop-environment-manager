"""
EnvironmentsCatalog Unit for Desktop Environment Manager UI.

Catalog screen displaying all available environments stored in the system.
Allows selecting an environment to manage it, or creating a new environment
via a two-step wizard using InputScreen.
"""

from __future__ import annotations

from typing import Any, Callable

from src.entities.context import AppContext
from src.entities.models import Environment
from src.services import component as component_service
from src.services import environment as environment_service
from src.ui.templates import (
    DropdownInputField,
    InputScreen,
    MenuOption,
    MenuScreen,
    MultiSelectInputField,
    TextInputField,
)
from src.ui.units.EnvironmentMenu import EnvironmentMenu


class EnvironmentsCatalog(MenuScreen):
    """
    Menu unit listing all registered environments and providing an add/create action.

    Selecting any environment transitions to its EnvironmentMenu.
    Selecting '+ Create Environment' starts a two-step creation flow:
        Step 1: Name, Type (Dynamic / Static), and Bound Components.
        Step 2: (Static only) Dropdown selection of available profile per bound component.
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
            title="Environments Catalog",
            options=self._build_options(),
            subtitle="Select an environment to view details or switch state, or create a new one below",
            can_go_back=can_go_back,
            on_back=on_back,
            name=name,
            id=id,
            classes=classes,
        )

    def _build_options(self) -> list[MenuOption]:
        """Build menu options from environments discovered in AppContext + Create Environment button."""
        environments = environment_service.get_environments(self.ctx)
        options: list[MenuOption] = []

        # Existing environments
        for env in environments.values():
            e_name = env.name
            is_active = self.ctx.environment == e_name
            type_label = "Dynamic" if env.dynamic else "Static"
            desc = f"Type: {type_label} | Bound: {len(env.bound_components)} components"
            if is_active:
                desc = f"(Active) {desc}"

            title = f"{env.display_name} (Active)" if is_active else env.display_name
            options.append(
                MenuOption(
                    title=title,
                    description=desc,
                    action=lambda target_name=e_name: self._open_environment_menu(
                        target_name
                    ),
                )
            )

        # Bottom-most option: Create Environment
        options.append(
            MenuOption(
                title="+ Create Environment",
                description="Configure a new static or dynamic automation environment",
                action=self._open_create_environment_step1,
            )
        )

        return options

    def refresh_environments(self) -> None:
        """Reload environments from backend and update menu options."""
        self.set_options(self._build_options())

    def on_screen_resume(self) -> None:
        """Refresh environments when returning to this catalog."""
        self.refresh_environments()

    def _open_environment_menu(self, environment_name: str) -> None:
        """Open the EnvironmentMenu for the selected environment."""
        environment_menu = EnvironmentMenu(
            ctx=self.ctx,
            environment_name=environment_name,
            on_deleted=self.refresh_environments,
        )
        self.app.push_screen(environment_menu)

    # --------------------------------------------------------------------------
    # Environment Creation Wizard (Step 1 & Step 2)
    # --------------------------------------------------------------------------

    def _open_create_environment_step1(self) -> None:
        """Step 1: Input name, environment type (Dynamic vs Static), and bound components."""
        components = list(self.ctx._components.values())
        if not components:
            self.notify(
                "No components are registered in AppContext to bind.",
                title="Cannot Create Environment",
                severity="error",
            )
            return

        comp_options = [(comp.DISPLAY_NAME, comp.NAME, True) for comp in components]

        fields = [
            TextInputField(
                key="display_name",
                label="Environment Name",
                description="Display name for the new environment",
                placeholder="e.g. Workstation-Triple",
                required=True,
            ),
            DropdownInputField(
                key="is_dynamic",
                label="Environment Type",
                description="Dynamic environments preserve state changes by auto-recapturing on exit; Static uses fixed profiles",
                options=[
                    ("Static (Uses fixed predefined profiles)", False),
                    ("Dynamic (Preserves changes by auto-recapturing on exit)", True),
                ],
                default=False,
                allow_blank=False,
                required=True,
            ),
            MultiSelectInputField(
                key="bound_components",
                label="Bound Components",
                options=comp_options,
                description="Select components to bind to this environment (Space to toggle)",
                required=True,
            ),
        ]

        def on_step1_submit(values: dict[str, Any]) -> None:
            display_name = values["display_name"].strip()
            is_dynamic = bool(values["is_dynamic"])
            bound_components = list(values.get("bound_components") or [])

            if not bound_components:
                self.notify(
                    "You must select at least one bound component.",
                    title="Validation Error",
                    severity="error",
                )
                return

            if is_dynamic:
                # Step 2 is skipped if dynamic: nothing passed for profile_mapping
                def task() -> None:
                    new_env = Environment.create_from_display_name(
                        display_name=display_name,
                        dynamic=True,
                        bound_components=bound_components,
                    )
                    environment_service.create_environment(self.ctx, new_env)

                def on_success(_) -> None:
                    self.notify(
                        f"Dynamic environment '{display_name}' created successfully.",
                        title="Environment Created",
                        severity="information",
                    )
                    self.refresh_environments()

                self.run_with_loading(
                    task=task,
                    title="Creating Environment",
                    status=f"Configuring dynamic environment '{display_name}'...",
                    on_success=on_success,
                )
            else:
                # Static environment: proceed to Step 2 to select profiles per bound component
                self._open_create_environment_step2(display_name, bound_components)

        step1_screen = InputScreen(
            title="Create Environment (Step 1 of 2)",
            subtitle="Configure environment name, operating type, and component bindings",
            fields=fields,
            submit_label="Next",
            cancel_label="Cancel",
            on_submit=on_step1_submit,
        )
        self.app.push_screen(step1_screen)

    def _open_create_environment_step2(
        self, display_name: str, bound_components: list[str]
    ) -> None:
        """
        Step 2 (Static environments only):
        Display a dropdown of available profiles for each bound component.
        """
        step2_fields: list[DropdownInputField] = []

        # Validate each bound component has at least one profile
        for comp_name in bound_components:
            comp = self.ctx.get_component(comp_name)
            profiles = component_service.get_profiles(self.ctx, comp_name)

            if not profiles:
                self.notify(
                    f"Component '{comp.DISPLAY_NAME}' has no saved profiles. "
                    f"Create a profile for it first before creating a static environment.",
                    title="Missing Profiles",
                    severity="error",
                )
                return

            profile_options = [(p.display_name, p.name) for p in profiles.values()]

            step2_fields.append(
                DropdownInputField(
                    key=comp_name,
                    label=f"{comp.DISPLAY_NAME} Profile",
                    description=f"Choose the profile to apply for {comp.DISPLAY_NAME}",
                    options=profile_options,
                    default=profile_options[0][1],
                    allow_blank=False,
                    required=True,
                )
            )

        def on_step2_submit(values: dict[str, Any]) -> None:
            profile_mapping = {
                comp_name: values[comp_name] for comp_name in bound_components
            }

            def task() -> None:
                new_env = Environment.create_from_display_name(
                    display_name=display_name,
                    dynamic=False,
                    bound_components=bound_components,
                    profile_mapping=profile_mapping,
                )
                environment_service.create_environment(self.ctx, new_env)

            def on_success(_) -> None:
                self.notify(
                    f"Static environment '{display_name}' created successfully.",
                    title="Environment Created",
                    severity="information",
                )
                self.refresh_environments()

            self.run_with_loading(
                task=task,
                title="Creating Environment",
                status=f"Configuring static environment '{display_name}'...",
                on_success=on_success,
            )

        step2_screen = InputScreen(
            title=f"Assign Profiles: {display_name} (Step 2 of 2)",
            subtitle="Select the profile used by this environment for each bound component",
            fields=step2_fields,
            submit_label="Create Environment",
            cancel_label="Cancel",
            on_submit=on_step2_submit,
        )
        self.app.push_screen(step2_screen)
