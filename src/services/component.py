from src.entities.component import Component
from src.entities.models import Profile, ComponentState
from src.entities.context import AppContext, ComponentContext
from src.storage.state_handler import StateHandler
from src.util.time import get_now_millis


def _component_sub_path(component_name: str) -> str:
    return f"components/{component_name}"


def _profiles_sub_path(component_name: str) -> str:
    return f"{_component_sub_path(component_name)}/profiles"


def _profile_sub_path(component_name: str, profile_name: str) -> str:
    return f"{_profiles_sub_path(component_name)}/{profile_name}"


def _storage_sub_path(component_name: str) -> str:
    return f"{_component_sub_path(component_name)}/storage"


def _get_component_context(ctx: AppContext, component: Component) -> ComponentContext:
    component_storage = ctx.data_dir.sub_handler(_storage_sub_path(component.NAME))
    profiles_storage = ctx.data_dir.sub_handler(_profiles_sub_path(component.NAME))
    return ComponentContext(
        component=component,
        component_storage=component_storage,
        profiles_storage=profiles_storage,
    )


def get_component_state(ctx: AppContext, component_name: str) -> ComponentState:
    component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))
    return StateHandler[ComponentState](component_dir).get_state()


def set_component_profile(
    ctx: AppContext, component_name: str, profile_name: str
) -> None:
    component = ctx.get_component(component_name)
    component_ctx = _get_component_context(ctx, component)
    component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))

    with StateHandler[ComponentState](component_dir) as component_state:
        if component_state.env_locked:
            raise ValueError(
                "cannot change component profile because it is "
                "set by an active dynamic environment"
            )

        if component_state.active_profile is not None:
            cur_profile = get_profiles(ctx, component_name).get(
                component_state.active_profile
            )
            if cur_profile is not None:
                success = component.exit_profile(cur_profile, component_ctx)
                if success is not None and success != 0:
                    raise RuntimeError(
                        f"failed to exit profile '{cur_profile.display_name}' "
                        f"on component '{component.DISPLAY_NAME}'"
                    )
            component_state.active_profile = None

        new_profile = get_profiles(ctx, component_name).get(profile_name)
        if new_profile is None:
            raise ValueError(
                f"profile '{profile_name}' not found for component '{component.DISPLAY_NAME}'"
            )

        success = component.enter_profile(new_profile, component_ctx)
        if success is not None and success != 0:
            raise RuntimeError(
                f"failed to switch component '{component.DISPLAY_NAME}' to "
                f"profile '{new_profile.display_name}'"
            )

        component_state.active_profile = profile_name


def get_profiles(ctx: AppContext, component_name: str) -> dict[str, Profile]:
    profiles_dir = ctx.data_dir.sub_handler(_profiles_sub_path(component_name))
    profiles: dict[str, Profile] = {}
    for entry in profiles_dir.scan_dir():
        handler = StateHandler[Profile](entry)
        if handler.has_state():
            profile = handler.get_state()
            profiles[profile.name] = profile
    return profiles


def get_profile_file_path(
    ctx: AppContext, component_name: str, profile_name: str
) -> str:
    component = ctx.get_component(component_name)
    profiles = get_profiles(ctx, component_name)
    if profile_name not in profiles:
        raise ValueError(
            f"profile '{profile_name}' not found for component '{component.DISPLAY_NAME}'"
        )
    profile = profiles[profile_name]
    return str(_get_component_context(ctx, component).profile_file_path(profile))


def create_profile(ctx: AppContext, component_name: str, profile: Profile) -> None:
    component = ctx.get_component(component_name)
    component_context = _get_component_context(ctx, component)
    component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))

    if StateHandler[ComponentState](component_dir).has_state():
        if StateHandler[ComponentState](component_dir).get_state().env_locked:
            raise ValueError(
                f"cannot create profile for component '{component.DISPLAY_NAME}' "
                "because it is locked by an active dynamic environment"
            )

    if profile.name in get_profiles(ctx, component_name):
        raise ValueError(
            f"component {component.DISPLAY_NAME} already has a "
            f"profile called {profile.display_name} (or something similar)"
        )

    profile_dir = ctx.data_dir.sub_handler(
        _profile_sub_path(component_name, profile.name)
    )
    StateHandler[Profile](profile_dir).set_state(profile)

    try:
        success = component.capture_profile(profile, component_context)
        if success is not None and success != 0:
            raise RuntimeError(
                f"failed to create new profile '{profile.display_name}' "
                f"for component '{component.DISPLAY_NAME}'"
            )
    except Exception:
        profile_dir.delete_relative()
        raise


def delete_profile(ctx: AppContext, component_name: str, profile_name: str) -> None:
    component = ctx.get_component(component_name)
    component_context = _get_component_context(ctx, component)
    component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))
    profile_dir = ctx.data_dir.sub_handler(
        _profile_sub_path(component_name, profile_name)
    )

    if not StateHandler[Profile](profile_dir).has_state():
        raise ValueError(
            f"profile '{profile_name}' does not exist for component '{component.DISPLAY_NAME}'"
        )

    with StateHandler[Profile](profile_dir) as profile:
        if profile.environment_usage_count > 0:
            raise ValueError(
                "cannot delete the profile - its used by "
                f"{profile.environment_usage_count} static environments"
            )
        display_name = profile.display_name

    if StateHandler[ComponentState](component_dir).has_state():
        with StateHandler[ComponentState](component_dir) as component_state:
            if component_state.active_profile == profile_name:
                cur_profile = get_profiles(ctx, component_name).get(profile_name)
                success = component.exit_profile(cur_profile, component_context)
                if success is not None and success != 0:
                    raise RuntimeError(
                        f"failed to exit profile '{display_name}' "
                        f"on component '{component.DISPLAY_NAME}'"
                    )
                component_state.active_profile = None

    profile_dir.delete_relative()


def recapture_profile(ctx: AppContext, component_name: str, profile_name: str) -> None:
    component = ctx.get_component(component_name)
    component_context = _get_component_context(ctx, component)
    component_dir = ctx.data_dir.sub_handler(_component_sub_path(component_name))
    profile_dir = ctx.data_dir.sub_handler(
        _profile_sub_path(component_name, profile_name)
    )

    if StateHandler[ComponentState](component_dir).has_state():
        if StateHandler[ComponentState](component_dir).get_state().env_locked:
            raise ValueError(
                f"cannot recapture profile for component '{component.DISPLAY_NAME}' "
                "because it is locked by an active dynamic environment"
            )

    profiles = get_profiles(ctx, component_name)
    if profile_name not in profiles:
        raise ValueError(
            f"profile '{profile_name}' not found for component '{component.DISPLAY_NAME}'"
        )
    profile = profiles[profile_name]

    success = component.capture_profile(profile, component_context)
    if success is not None and success != 0:
        raise RuntimeError(
            f"failed to recapture profile '{profile.display_name}' "
            f"for component '{component.DISPLAY_NAME}'"
        )

    with StateHandler[Profile](profile_dir) as profile_state:
        profile_state.last_capture_timestamp = get_now_millis()


def setup_components(ctx: AppContext) -> None:
    for component in ctx.components:
        component_context = _get_component_context(ctx, component)
        component_dir = ctx.data_dir.sub_handler(_component_sub_path(component.NAME))
        with StateHandler[ComponentState](component_dir) as component_state:
            if not component_state.setup:
                success = component.setup(component_context)
                if success is not None and success != 0:
                    raise RuntimeError(
                        f"failed to setup component '{component.DISPLAY_NAME}'"
                    )
                component_state.setup = True


def initialize_components(ctx: AppContext) -> None:
    for component in ctx.components:
        component_context = _get_component_context(ctx, component)
        success = component.init(component_context)
        if success is not None and success != 0:
            raise RuntimeError(
                f"failed to initialize component '{component.DISPLAY_NAME}'"
            )
