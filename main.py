from pathlib import Path
from typing import Iterator

from components import components as app_components
from src.ui.app import run_app
from src.entities.context import AppContext
from src.entities.models import AppState
from src.storage.state_handler import StateHandler
from src.services import component as component_service


DATA_PATH = Path(__file__).resolve().parent / "data"
APP_STATE_PATH = DATA_PATH / "app"


def get_app_context() -> AppContext:
    with StateHandler[AppState](APP_STATE_PATH) as app_state:
        active_env = app_state.active_environment

    return AppContext(
        data_dir=DATA_PATH,
        components=app_components,
        active_environment=active_env,
    )


def lifespan(ctx: AppContext) -> Iterator[None]:
    component_service.setup_components(ctx)
    component_service.initialize_components(ctx)

    yield  # The app is now running with the UI

    with StateHandler[AppState](APP_STATE_PATH) as app_state:
        app_state.active_environment = ctx.environment


def main() -> None:
    ctx = get_app_context()
    run_app(ctx=ctx, lifespan=lifespan)


if __name__ == "__main__":
    main()
