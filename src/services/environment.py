from typing import Optional

from src.services.component import (  # type: ignore
    _component_sub_path,
    _storage_sub_path,
    _profile_sub_path,
    _profiles_sub_path,
    get_profiles,
    _get_component_context as _get_standard_component_context,
)
from src.entities.context import AppContext, ComponentContext
from src.entities.models import Environment, Profile, ComponentState
from src.storage.state_handler import StateHandler


_ENVIRONMENT_PROFILE_NAME = "__env_profile__"
_ENVIRONMENT_PROFILE = Profile(
    name=_ENVIRONMENT_PROFILE_NAME,
    display_name=_ENVIRONMENT_PROFILE_NAME,
    creation_timestamp=-1,
    last_capture_timestamp=-1,
)


def _environments_sub_path() -> str:
    return "environments"


def _environment_sub_path(environment_name: str) -> str:
    return f"{_environments_sub_path()}/{environment_name}"


def _env_component_sub_path(environment_name: str, component_name: str) -> str:
    return (
        f"{_environment_sub_path(environment_name)}/bound_components/{component_name}"
    )


def _env_profile_sub_path(environment_name: str, component_name: str) -> str:
    return f"{_env_component_sub_path(environment_name, component_name)}/{_ENVIRONMENT_PROFILE_NAME}"


def _get_component_context(
    ctx: AppContext, environment: Environment, component_name: str
) -> ComponentContext:
    component = ctx.get_component(component_name)
    component_storage = ctx.data_dir.sub_handler(_storage_sub_path(component_name))
    # dynamic environments are routed to the env-specific profile storage.
    # static environments are routed to the component profile storage (to
    # allow usage of a standard profile)
    if environment.dynamic:
        profiles_storage = ctx.data_dir.sub_handler(
            _env_component_sub_path(environment.name, component_name)
        )
    else:
        profiles_storage = ctx.data_dir.sub_handler(_profiles_sub_path(component_name))
    return ComponentContext(
        component=component,
        component_storage=component_storage,
        profiles_storage=profiles_storage,
    )


def _get_component_profile(
    ctx: AppContext,
    environment: Environment,
    component_name: str,
    profile_name: Optional[str],
) -> Profile:
    component = ctx.get_component(component_name)
    if environment.dynamic:
        return _ENVIRONMENT_PROFILE

    if profile_name is None:
        raise RuntimeError(
            f"expected setup profile for bound component '{component.DISPLAY_NAME}' "
            f"in environment '{environment.display_name}'"
        )

    profiles = get_profiles(ctx, component_name)
    if profile_name not in profiles:
        raise RuntimeError(
            f"profile '{profile_name}' not found for bound component '{component.DISPLAY_NAME}'"
        )

    return profiles[profile_name]


def get_environments(ctx: AppContext) -> dict[str, Environment]:
    environments_dir = ctx.data_dir.sub_handler(_environments_sub_path())
    environments: dict[str, Environment] = {}
    for entry in environments_dir.scan_dir():
        handler = StateHandler[Environment](entry)
        if handler.has_state():
            environment = handler.get_state()
            environments[environment.name] = environment
    return environments


def create_environment(ctx: AppContext, environment: Environment) -> None:
    if environment.name in get_environments(ctx):
        raise ValueError(
            f"environment '{environment.display_name}' already exists (identifier: '{environment.name}')"
        )

    # if static environment - validate all bound components have valid profiles before writing
    if not environment.dynamic:
        for component_name in environment.bound_components:
            component = ctx.get_component(component_name)
            profiles = get_profiles(ctx, component_name)
            selected_profile = environment.profile_mapping.get(component_name)
            if selected_profile is None:
                raise ValueError(
                    f"bound component '{component.DISPLAY_NAME}' has no selected profile"
                )
            if selected_profile not in profiles:
                raise ValueError(
                    f"bound component '{component.DISPLAY_NAME}' selected "
                    f"invalid profile '{selected_profile}'"
                )

    environment_dir = ctx.data_dir.sub_handler(_environment_sub_path(environment.name))
    StateHandler[Environment](environment_dir).set_state(environment)

    if not environment.dynamic:
        for component_name in environment.bound_components:
            selected_profile = environment.profile_mapping[component_name]
            profile_dir = ctx.data_dir.sub_handler(
                _profile_sub_path(component_name, selected_profile)
            )
            with StateHandler[Profile](profile_dir) as profile:
                profile.environment_usage_count += 1
        return

    # if dynamic environment - capture the env profiles from the current system configuration
    try:
        for component_name in environment.bound_components:
            component = ctx.get_component(component_name)
            component_ctx = _get_component_context(ctx, environment, component_name)

            profile_dir = ctx.data_dir.sub_handler(
                _env_profile_sub_path(environment.name, component_name)
            )
            profile_dir.assert_directory_exists()
            StateHandler[Profile](profile_dir).set_state(_ENVIRONMENT_PROFILE)

            success = component.capture_profile(_ENVIRONMENT_PROFILE, component_ctx)
            if success is not None and success != 0:
                raise RuntimeError(
                    "failed to capture environment profile of environment "
                    f"'{environment.display_name}' for component '{component.DISPLAY_NAME}'"
                )
    except Exception:
        environment_dir.delete_relative()
        raise


def enter_environment(ctx: AppContext, environment_name: str) -> None:
    exit_cur_environment(ctx)

    environments = get_environments(ctx)
    if environment_name not in environments:
        raise ValueError(f"environment '{environment_name}' does not exist")
    environment = environments[environment_name]

    for component_name in environment.bound_components:
        component = ctx.get_component(component_name)
        component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))
        component_ctx = _get_component_context(ctx, environment, component_name)
        profile_name = environment.profile_mapping.get(component_name)
        profile = _get_component_profile(ctx, environment, component_name, profile_name)

        with StateHandler[ComponentState](component_dir) as component_state:
            if component_state.active_profile is not None:
                active_profile = get_profiles(ctx, component_name).get(
                    component_state.active_profile
                )
                if active_profile is not None:
                    # Exit previous profile using the standard component context
                    old_comp_ctx = _get_standard_component_context(ctx, component)
                    success = component.exit_profile(active_profile, old_comp_ctx)
                    if success is not None and success != 0:
                        raise RuntimeError(
                            "failed to exit active profile for component "
                            f"'{component.DISPLAY_NAME}'"
                        )
                component_state.active_profile = None

            success = component.enter_profile(profile, component_ctx)
            if success is not None and success != 0:
                raise RuntimeError(
                    "failed to enter environment profile of environment "
                    f"'{environment.display_name}' for component '{component.DISPLAY_NAME}'"
                )

            # only lock the component from modifications if the active
            # environment is dynamic
            component_state.env_locked = environment.dynamic
            component_state.active_profile = profile_name

    # keep environment as active only if it is dynamic
    if environment.dynamic:
        ctx.environment = environment_name


def exit_cur_environment(ctx: AppContext) -> None:
    if ctx.environment is None:
        return

    environment = get_environments(ctx).get(ctx.environment)
    if environment is None:
        ctx.environment = None
        return

    if not environment.dynamic:
        raise Exception(
            "unexpected: static environments shouldn't be registered "
            "as active environments"
        )

    errors: list[str] = []
    for component_name in environment.bound_components:
        component = ctx.get_component(component_name)
        component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))
        component_ctx = _get_component_context(ctx, environment, component_name)

        try:
            success = component.capture_profile(_ENVIRONMENT_PROFILE, component_ctx)
            if success is not None and success != 0:
                errors.append(
                    f"failed to capture environment profile for '{component.DISPLAY_NAME}'"
                )
        except Exception as e:
            errors.append(
                f"error capturing environment profile for '{component.DISPLAY_NAME}': {e}"
            )

        try:
            success = component.exit_profile(_ENVIRONMENT_PROFILE, component_ctx)
            if success is not None and success != 0:
                errors.append(
                    f"failed to exit environment profile for '{component.DISPLAY_NAME}'"
                )
        except Exception as e:
            errors.append(
                f"error exiting environment profile for '{component.DISPLAY_NAME}': {e}"
            )

        if StateHandler[ComponentState](component_dir).has_state():
            with StateHandler[ComponentState](component_dir) as component_state:
                component_state.env_locked = False
                component_state.active_profile = None

    ctx.environment = None

    if errors:
        raise RuntimeError(
            f"Errors occurred while exiting environment '{environment.display_name}': "
            + "; ".join(errors)
        )


def delete_environment(ctx: AppContext, environment_name: str) -> None:
    if environment_name == ctx.environment:
        exit_cur_environment(ctx)

    environments = get_environments(ctx)
    if environment_name not in environments:
        raise ValueError(f"environment '{environment_name}' does not exist")
    environment = environments[environment_name]

    # if static - decrease profile usage counts
    if not environment.dynamic:
        for component_name in environment.bound_components:
            selected_profile = environment.profile_mapping.get(component_name)
            if selected_profile is not None:
                profile_dir = ctx.data_dir.sub_handler(
                    _profile_sub_path(component_name, selected_profile)
                )
                if StateHandler[Profile](profile_dir).has_state():
                    with StateHandler[Profile](profile_dir) as profile:
                        profile.environment_usage_count = max(
                            0, profile.environment_usage_count - 1
                        )

    environment_storage = ctx.data_dir.sub_handler(
        _environment_sub_path(environment_name)
    )
    environment_storage.delete_relative()
