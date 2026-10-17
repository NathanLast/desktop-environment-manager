from src.entities.component import Component

from components.windows.monitor import MonitorComponent
from components.windows.sound import SoundComponent

components: list[Component] = [MonitorComponent(), SoundComponent()]
