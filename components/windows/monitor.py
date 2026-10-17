from pathlib import Path

from src.entities.component import Component, SuccessStatus
from src.entities.models import Profile
from src.entities.context import ComponentContext
from src.util.nirsoft_constants import NIRSOFT_SOFTWARE_BASE_DOWNLOAD_LINK
from src.util.system import run_command
from src.util.web import download_zip

MMT_SOFTWARE_NAME = "multimonitortool-x64"
MMT_SOFTWARE_ZIP_NAME = f"{MMT_SOFTWARE_NAME}.zip"
MMT_EXE_NAME = "MultiMonitorTool.exe"

MMT_SAVE_CONFIG_COMMAND = "/SaveConfig"
MMT_LOAD_CONFIG_COMMAND = "/LoadConfig"

MMT_EXE_REL_PATH = Path() / MMT_SOFTWARE_NAME / MMT_EXE_NAME

MMT_REMOTE_LINK = f"{NIRSOFT_SOFTWARE_BASE_DOWNLOAD_LINK}/{MMT_SOFTWARE_ZIP_NAME}"


class MonitorComponent(Component):
    NAME = "monitor"
    DISPLAY_NAME = "Monitor"
    EXTENSION = "cfg"

    def enter_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        return run_command(
            exe_path=ctx.storage().get_full_path(MMT_EXE_REL_PATH),
            args=[MMT_LOAD_CONFIG_COMMAND, ctx.profile_file_path(profile)],
        )

    def exit_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        pass

    def capture_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        return run_command(
            exe_path=ctx.storage().get_full_path(MMT_EXE_REL_PATH),
            args=[MMT_SAVE_CONFIG_COMMAND, ctx.profile_file_path(profile)],
        )

    def setup(self, ctx: ComponentContext) -> SuccessStatus:
        zip_path = ctx.storage().get_full_path(MMT_SOFTWARE_ZIP_NAME)

        return download_zip(
            remote_link=MMT_REMOTE_LINK, local_path=zip_path, auto_unzip=True
        )
