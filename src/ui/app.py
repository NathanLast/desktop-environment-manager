"""
Main Application Entrypoint for Desktop Environment Manager UI.

Houses the root MainMenu displaying options for Components Catalog and Environments Catalog.
Receives an AppContext instance and an optional startup/shutdown lifespan generator.
During initialization (before yield), a LoadingScreen is displayed. If initialization fails,
an internal ErrorScreen is presented allowing the user only to exit.
Upon exit (if initialization succeeded), the remainder of the lifespan generator (after yield)
is executed for finalization/cleanup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator, Optional

from textual.app import App
from textual.binding import Binding

from src.entities.context import AppContext
from src.ui.templates import Menu, MenuOption
from src.ui.units import ComponentsCatalog, EnvironmentsCatalog, LoadingScreen
from src.ui.units.ErrorScreen import ErrorScreen

TCSS_PATH = Path(__file__).resolve().parent / "style.tcss"


def _create_default_context() -> AppContext:
    """
    Fallback helper to build a default AppContext when running directly.
    Will later be provided by the system's app initializer.
    """
    try:
        from components import components
    except Exception:
        components = []

    # Default data directory in workspace or user profile
    data_dir = Path(__file__).resolve().parents[3] / "profiles"
    return AppContext(data_dir=data_dir, components=components, active_environment=None)


class AutomationApp(App):
    """
    Main Desktop Environment Manager Application.

    Accepts a lifespan lifecycle generator/function (runs startup before yield, cleanup after yield).
    While initializing, displays LoadingScreen. If initialization fails, switches to ErrorScreen.
    Upon successful initialization, transitions into the root MainMenu.
    When exiting the application, executes the finalization portion (after yield).
    """

    CSS_PATH = TCSS_PATH
    TITLE = "Desktop Environment Manager"
    SUB_TITLE = "Main System Menu"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Exit", show=True, priority=True),
    ]

    def __init__(
        self,
        ctx: Optional[AppContext] = None,
        lifespan: Optional[Callable[[AppContext], Iterator[None]]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._ctx: Optional[AppContext] = ctx
        self._lifespan: Optional[Callable[[AppContext], Iterator[None]]] = lifespan
        self._lifespan_gen: Optional[Iterator[None]] = None
        self._init_succeeded: bool = False

    @property
    def ctx(self) -> AppContext:
        """Lazily obtain AppContext so app can start without premature context errors."""
        if self._ctx is None:
            self._ctx = _create_default_context()
        return self._ctx

    @ctx.setter
    def ctx(self, context: AppContext) -> None:
        self._ctx = context

    def on_mount(self) -> None:
        """
        Mount startup screen:
        If lifespan provided, display LoadingScreen and execute startup (before yield) in background.
        Otherwise, mount root MainMenu directly.
        """
        if self._lifespan is not None:
            self.push_screen(LoadingScreen())
            self.run_worker(self._perform_sync_init, thread=True, exclusive=True)
        else:
            self.push_screen(self._create_main_menu())

    def _perform_sync_init(self) -> None:
        """Worker thread executing startup phase of the lifespan lifecycle."""
        try:
            if self._lifespan is not None:
                self._lifespan_gen = self._lifespan(self.ctx)
                next(self._lifespan_gen)
            self._init_succeeded = True
            self.call_from_thread(self._on_init_success)
        except Exception as exc:
            self._init_succeeded = False
            self.call_from_thread(self._on_init_failure, str(exc))

    def _on_init_success(self) -> None:
        """Transition from LoadingScreen to the root MainMenu."""
        self.switch_screen(self._create_main_menu())

    def _on_init_failure(self, error_message: str) -> None:
        """Transition to ErrorScreen presenting the initialization failure."""
        self.switch_screen(ErrorScreen(error_message))

    def run_with_loading(
        self,
        task: Callable[[], Any],
        title: str = "Please Wait",
        status: str = "Executing operation...",
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> None:
        """
        Execute a long-running service task in a worker thread while displaying LoadingScreen.
        Upon completion or failure, the LoadingScreen is dismissed and on_success / on_error is called.
        """
        loading = LoadingScreen(title=title, status=status)
        self.push_screen(loading)

        def worker() -> None:
            try:
                result = task()
                self.call_from_thread(
                    self._on_loading_task_done, loading, on_success, result
                )
            except Exception as exc:
                self.call_from_thread(
                    self._on_loading_task_error, loading, on_error, exc
                )

        self.run_worker(worker, thread=True)

    def _on_loading_task_done(
        self,
        loading: LoadingScreen,
        on_success: Optional[Callable[[Any], Any]],
        result: Any,
    ) -> None:
        loading.dismiss()
        if on_success is not None:
            on_success(result)

    def _on_loading_task_error(
        self,
        loading: LoadingScreen,
        on_error: Optional[Callable[[Exception], Any]],
        exc: Exception,
    ) -> None:
        loading.dismiss()
        if on_error is not None:
            on_error(exc)
        else:
            self.notify(str(exc), title="Operation Failed", severity="error")

    def on_unmount(self) -> None:
        """
        Execute the finalization stage of the lifespan generator on app exit
        (only if initialization completed without error).
        """
        if self._init_succeeded and self._lifespan_gen is not None:
            try:
                next(self._lifespan_gen)
            except StopIteration:
                pass
            except Exception:
                pass
            finally:
                self._lifespan_gen = None

    def _create_main_menu(self) -> Menu:
        """Create the root main menu with Components and Environments catalog options."""
        options = [
            MenuOption(
                title="Components Catalog",
                description="Browse available components, manage profiles, and capture new states",
                action=self._open_components_catalog,
            ),
            MenuOption(
                title="Environments Catalog",
                description="View and activate automation environments across bound components",
                action=self._open_environments_catalog,
            ),
        ]
        return Menu(
            title="Desktop Environment Manager",
            subtitle="Main Menu",
            options=options,
            can_go_back=False,
        )

    def _open_components_catalog(self) -> None:
        """Transition to the ComponentsCatalog unit."""
        self.push_screen(ComponentsCatalog(self.ctx))

    def _open_environments_catalog(self) -> None:
        """Transition to the EnvironmentsCatalog unit."""
        self.push_screen(EnvironmentsCatalog(self.ctx))


def run_app(
    ctx: Optional[AppContext] = None,
    lifespan: Optional[Callable[[AppContext], Iterator[None]]] = None,
) -> None:
    """Helper entrypoint to instantiate and run AutomationApp."""
    app = AutomationApp(ctx=ctx, lifespan=lifespan)
    app.run()


if __name__ == "__main__":
    run_app()
