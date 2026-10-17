"""
InputScreen Template for Desktop Environment Manager UI.

A generic form screen template that gathers user input from modular InputField
components (e.g., text, dropdown, toggle, integer, textarea).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Sequence

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    Select,
    SelectionList,
    Switch,
    TextArea,
)
from textual.widgets.selection_list import Selection

TCSS_PATH = Path(__file__).resolve().parent.parent / "style.tcss"


# ==============================================================================
# Abstract & Concrete Input Field Definitions
# ==============================================================================


class InputField(ABC):
    """
    Abstract base class for all form input methods.

    Attributes:
        key: The parameter name/identifier for the value being collected.
        label: The user-facing label shown above the input widget.
        description: Optional helpful context or instructions shown below the input.
        required: Whether the input must be non-empty upon submission.
        default: Initial value populated into the widget.
    """

    def __init__(
        self,
        key: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: Any = None,
    ) -> None:
        self.key = key
        self.label = label
        self.description = description
        self.required = required
        self.default = default
        self._widget: Widget | None = None

    @abstractmethod
    def build_widget(self) -> Widget:
        """Create and configure the underlying Textual widget."""
        ...

    @abstractmethod
    def get_value(self) -> Any:
        """Extract and return the current value from the widget."""
        ...

    def set_value(self, value: Any) -> None:
        """Set or update the value in the underlying widget if mounted."""
        self.default = value

    def validate(self) -> str | None:
        """
        Validate current field value.

        Returns:
            Error message string if validation fails, or None if valid.
        """
        if self.required:
            val = self.get_value()
            if val is None or val == "" or (isinstance(val, (list, dict)) and not val):
                return f"'{self.label}' is required."
        return None


class TextInputField(InputField):
    """Text input field for single-line strings."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: str = "",
        placeholder: str = "",
        password: bool = False,
        max_length: int | None = None,
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=required,
            default=default,
        )
        self.placeholder = placeholder
        self.password = password
        self.max_length = max_length
        self._input_widget: Input | None = None

    def build_widget(self) -> Widget:
        self._input_widget = Input(
            value=str(self.default or ""),
            placeholder=self.placeholder,
            password=self.password,
            max_length=self.max_length,
            classes="field-widget",
            id=f"input-{self.key}",
        )
        self._widget = self._input_widget
        return self._input_widget

    def get_value(self) -> str:
        if self._input_widget is not None:
            return self._input_widget.value.strip()
        return str(self.default or "")

    def set_value(self, value: Any) -> None:
        super().set_value(value)
        if self._input_widget is not None:
            self._input_widget.value = str(value)


class DropdownInputField(InputField):
    """Dropdown selection field using Select."""

    def __init__(
        self,
        key: str,
        label: str,
        options: Sequence[tuple[str, Any]] | Sequence[str],
        description: str = "",
        required: bool = False,
        default: Any = None,
        prompt: str = "Select an option...",
        allow_blank: bool = True,
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=required,
            default=default,
        )
        self.prompt = prompt
        self.allow_blank = allow_blank

        # Normalize options to (label, value) tuples
        normalized: list[tuple[str, Any]] = []
        for opt in options:
            if isinstance(opt, tuple) and len(opt) == 2:
                normalized.append((str(opt[0]), opt[1]))
            else:
                normalized.append((str(opt), opt))
        self.options = normalized
        self._select_widget: Select[Any] | None = None

    def build_widget(self) -> Widget:
        initial_val = self.default
        if initial_val is None and not self.allow_blank and self.options:
            initial_val = self.options[0][1]

        self._select_widget = Select[Any](
            options=self.options,
            value=initial_val if initial_val is not None else Select.NULL,
            prompt=self.prompt,
            allow_blank=self.allow_blank,
            classes="field-widget",
            id=f"select-{self.key}",
        )
        self._widget = self._select_widget
        return self._select_widget

    def get_value(self) -> Any:
        if self._select_widget is not None:
            val = self._select_widget.value
            if (
                val is Select.NULL
                or getattr(self._select_widget, "is_blank", lambda: False)()
            ):
                return None
            return val
        return self.default

    def set_value(self, value: Any) -> None:
        super().set_value(value)
        if self._select_widget is not None:
            self._select_widget.value = value


class ToggleInputField(InputField):
    """Boolean toggle/switch field."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str = "",
        default: bool = False,
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=False,
            default=bool(default),
        )
        self._switch_widget: Switch | None = None

    def build_widget(self) -> Widget:
        self._switch_widget = Switch(
            value=bool(self.default),
            classes="field-widget",
            id=f"switch-{self.key}",
        )
        self._widget = self._switch_widget
        return self._switch_widget

    def get_value(self) -> bool:
        if self._switch_widget is not None:
            return bool(self._switch_widget.value)
        return bool(self.default)

    def set_value(self, value: Any) -> None:
        super().set_value(bool(value))
        if self._switch_widget is not None:
            self._switch_widget.value = bool(value)


class IntegerInputField(InputField):
    """Integer numeric input field."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
        placeholder: str = "",
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=required,
            default=default,
        )
        self.min_value = min_value
        self.max_value = max_value
        self.placeholder = placeholder
        self._input_widget: Input | None = None

    def build_widget(self) -> Widget:
        self._input_widget = Input(
            value=str(self.default) if self.default is not None else "",
            placeholder=self.placeholder,
            type="integer",
            classes="field-widget",
            id=f"input-{self.key}",
        )
        self._widget = self._input_widget
        return self._input_widget

    def get_value(self) -> int | None:
        if self._input_widget is not None:
            val_str = self._input_widget.value.strip()
            if not val_str:
                return None
            try:
                return int(val_str)
            except ValueError:
                return None
        return self.default

    def validate(self) -> str | None:
        base_err = super().validate()
        if base_err:
            return base_err

        val = self.get_value()
        if val is None:
            if self._input_widget and self._input_widget.value.strip():
                return f"'{self.label}' must be a valid integer."
            return None

        if self.min_value is not None and val < self.min_value:
            return f"'{self.label}' cannot be less than {self.min_value}."
        if self.max_value is not None and val > self.max_value:
            return f"'{self.label}' cannot be greater than {self.max_value}."
        return None

    def set_value(self, value: Any) -> None:
        super().set_value(value)
        if self._input_widget is not None:
            self._input_widget.value = str(value) if value is not None else ""


class TextAreaInputField(InputField):
    """Multi-line text input field."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: str = "",
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=required,
            default=default,
        )
        self._text_area: TextArea | None = None

    def build_widget(self) -> Widget:
        self._text_area = TextArea(
            text=str(self.default or ""),
            classes="field-widget",
            id=f"textarea-{self.key}",
        )
        self._widget = self._text_area
        return self._text_area

    def get_value(self) -> str:
        if self._text_area is not None:
            return self._text_area.text
        return str(self.default or "")

    def set_value(self, value: Any) -> None:
        super().set_value(value)
        if self._text_area is not None:
            self._text_area.text = str(value)


class MultiSelectInputField(InputField):
    """Multiple selection list field using Textual SelectionList."""

    def __init__(
        self,
        key: str,
        label: str,
        options: Sequence[tuple[str, Any, bool] | tuple[str, Any] | str],
        description: str = "",
        required: bool = False,
    ) -> None:
        super().__init__(
            key=key,
            label=label,
            description=description,
            required=required,
            default=[],
        )
        self.options = options
        self._selection_widget: SelectionList[Any] | None = None

    def build_widget(self) -> Widget:
        selections: list[Selection[Any]] = []
        for opt in self.options:
            if isinstance(opt, tuple):
                if len(opt) == 3:
                    selections.append(
                        Selection(str(opt[0]), opt[1], initial_state=bool(opt[2]))
                    )
                elif len(opt) == 2:
                    selections.append(
                        Selection(str(opt[0]), opt[1], initial_state=False)
                    )
            else:
                selections.append(Selection(str(opt), opt, initial_state=False))

        self._selection_widget = SelectionList[Any](
            *selections,
            classes="field-widget",
            id=f"selectlist-{self.key}",
        )
        self._widget = self._selection_widget
        return self._selection_widget

    def get_value(self) -> list[Any]:
        if self._selection_widget is not None:
            return list(self._selection_widget.selected)
        return []

    def validate(self) -> str | None:
        if self.required and not self.get_value():
            return f"At least one '{self.label}' must be selected."
        return None


# Alternative naming aliases for flexibility
InputMethod = InputField
TextInputMethod = TextInputField
DropdownInputMethod = DropdownInputField
ToggleInputMethod = ToggleInputField
IntegerInputMethod = IntegerInputField
TextAreaInputMethod = TextAreaInputField
MultiSelectInputMethod = MultiSelectInputField
SelectInputField = DropdownInputField
SwitchInputField = ToggleInputField
SelectionListInputField = MultiSelectInputField


# ==============================================================================
# UI Component Wrapper for Input Fields
# ==============================================================================


class InputFieldContainer(Vertical):
    """Container wrapping a single InputField's label, widget, and error feedback."""

    def __init__(self, field: InputField, **kwargs: Any) -> None:
        super().__init__(classes="field-container", **kwargs)
        self.field = field

    def compose(self) -> ComposeResult:
        label_text = self.field.label
        if self.field.required:
            label_text += " *"
        yield Label(label_text, classes="field-label")
        yield self.field.build_widget()
        if self.field.description:
            yield Label(self.field.description, classes="field-description")
        yield Label("", classes="field-error", id=f"error-label-{self.field.key}")

    def show_error(self, message: str) -> None:
        """Display an error message for this specific input field."""
        err_label = self.query_one(f"#error-label-{self.field.key}", Label)
        err_label.update(message)
        err_label.add_class("visible")

    def clear_error(self) -> None:
        """Clear any active validation error message."""
        err_label = self.query_one(f"#error-label-{self.field.key}", Label)
        err_label.update("")
        err_label.remove_class("visible")


# ==============================================================================
# Main InputScreen Template
# ==============================================================================


class InputScreen(Screen[dict[str, Any] | None]):
    """
    Generic Input Screen template.

    Gathers user input across a list of InputField objects. Upon submission:
        - Validates all fields against constraints.
        - Exposes collected input through properties, callbacks, and dismissal value.
    """

    CSS_PATH = TCSS_PATH

    BINDINGS = [
        Binding("ctrl+s", "submit_form", "Submit", show=True),
        Binding("escape", "cancel_form", "Cancel", show=True),
        Binding("ctrl+q", "app.quit", "Exit", show=True, priority=True),
    ]

    class Submitted(Message):
        """Event posted when the form is successfully validated and submitted."""

        def __init__(self, values: dict[str, Any]) -> None:
            super().__init__()
            self.values = values

    class Cancelled(Message):
        """Event posted when the user cancels input collection."""

        pass

    def __init__(
        self,
        title: str,
        fields: Sequence[InputField],
        subtitle: str = "",
        submit_label: str = "Submit",
        cancel_label: str = "Cancel",
        on_submit: Callable[[dict[str, Any]], Any] | None = None,
        on_cancel: Callable[[], Any] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.screen_title = title
        self.subtitle = subtitle
        self.submit_label = submit_label
        self.cancel_label = cancel_label
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel

        self.fields: list[InputField] = list(fields)
        self._containers: list[InputFieldContainer] = []
        self._submitted_values: dict[str, Any] | None = None

    def compose(self) -> ComposeResult:
        with Container(id="input-screen-container"):
            with Vertical(id="screen-header"):
                yield Label(self.screen_title, id="screen-title")
                if self.subtitle:
                    yield Label(self.subtitle, id="screen-subtitle")

            with VerticalScroll(classes="form-scroll-container"):
                self._containers.clear()
                for field in self.fields:
                    container = InputFieldContainer(field)
                    self._containers.append(container)
                    yield container

            with Horizontal(id="screen-footer-container", classes="form-actions"):
                yield Button(
                    self.submit_label,
                    id="submit-button",
                    classes="btn-primary",
                )
                yield Button(
                    self.cancel_label,
                    id="cancel-button",
                    classes="btn-secondary",
                )

        yield Footer()

    # --------------------------------------------------------------------------
    # Value Access & State Exposure
    # --------------------------------------------------------------------------

    def get_values(self) -> dict[str, Any]:
        """Collect current values from all input fields as a dictionary."""
        return {field.key: field.get_value() for field in self.fields}

    @property
    def values(self) -> dict[str, Any]:
        """Convenience property returning current field values."""
        return self.get_values()

    @property
    def submitted_values(self) -> dict[str, Any] | None:
        """The final validated dictionary submitted by the user, or None if cancelled."""
        return self._submitted_values

    # --------------------------------------------------------------------------
    # Submission & Validation Logic
    # --------------------------------------------------------------------------

    def validate_form(self) -> bool:
        """
        Validate all input fields.

        Displays inline errors on failing fields.
        Returns True if all fields are valid, False otherwise.
        """
        is_valid = True
        first_invalid_widget: Widget | None = None

        for container in self._containers:
            error_message = container.field.validate()
            if error_message:
                container.show_error(error_message)
                is_valid = False
                if first_invalid_widget is None and container.field._widget is not None:
                    first_invalid_widget = container.field._widget
            else:
                container.clear_error()

        if first_invalid_widget is not None:
            first_invalid_widget.focus()

        return is_valid

    def action_submit_form(self) -> None:
        """Handle form submission."""
        if not self.validate_form():
            return

        values = self.get_values()
        self._submitted_values = values

        # Notify parent app/widget via message
        self.post_message(self.Submitted(values))

        # Dismiss screen returning collected dictionary
        self.dismiss(values)

        # Execute callback if provided after screen has dismissed
        if self.on_submit_callback:
            self.app.call_after_refresh(self.on_submit_callback, values)

    def action_cancel_form(self) -> None:
        """Handle form cancellation."""
        self.post_message(self.Cancelled())
        self.dismiss(None)

        if self.on_cancel_callback:
            self.app.call_after_refresh(self.on_cancel_callback)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click events."""
        if event.button.id == "submit-button":
            self.action_submit_form()
        elif event.button.id == "cancel-button":
            self.action_cancel_form()
