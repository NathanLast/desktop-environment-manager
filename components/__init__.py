import platform
import warnings

from src.entities.component import Component
from components.linux import components as linux_components
from components.macos import components as macos_components
from components.windows import components as windows_components


components: list[Component]
match platform.system():
    case "Linux":
        components = linux_components
    case "Darwin":
        components = macos_components
    case "Windows":
        components = windows_components
    case unknown:
        warnings.warn(f"unsupported platform '{unknown}'. no components are loaded")
        components = []
