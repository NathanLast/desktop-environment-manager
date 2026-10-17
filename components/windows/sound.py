from pathlib import Path

from src.entities.component import Component, SuccessStatus
from src.entities.models import Profile
from src.entities.context import ComponentContext
from src.util.nirsoft_constants import NIRSOFT_SOFTWARE_BASE_DOWNLOAD_LINK
from src.util.system import run_command
from src.util.web import download_zip

SVV_SOFTWARE_NAME = "soundvolumeview-x64"
SVV_SOFTWARE_ZIP_NAME = f"{SVV_SOFTWARE_NAME}.zip"
SVV_EXE_NAME = "SoundVolumeView.exe"

SVV_SAVE_PROFILE_COMMAND = "/SaveProfile"
SVV_LOAD_PROFILE_COMMAND = "/LoadProfile"

SVV_EXE_REL_PATH = Path() / SVV_SOFTWARE_NAME / SVV_EXE_NAME

SVV_REMOTE_LINK = f"{NIRSOFT_SOFTWARE_BASE_DOWNLOAD_LINK}/{SVV_SOFTWARE_ZIP_NAME}"


class SoundComponent(Component):
    NAME = "sound"
    DISPLAY_NAME = "Sound"
    EXTENSION = "spr"

    def enter_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        return run_command(
            exe_path=ctx.storage().get_full_path(SVV_EXE_REL_PATH),
            args=[SVV_LOAD_PROFILE_COMMAND, ctx.profile_file_path(profile)],
        )

    def exit_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        pass

    def capture_profile(self, profile: Profile, ctx: ComponentContext) -> SuccessStatus:
        return run_command(
            exe_path=ctx.storage().get_full_path(SVV_EXE_REL_PATH),
            args=[SVV_SAVE_PROFILE_COMMAND, ctx.profile_file_path(profile)],
        )

    def setup(self, ctx: ComponentContext) -> SuccessStatus:
        zip_path = ctx.storage().get_full_path(SVV_SOFTWARE_ZIP_NAME)

        return download_zip(
            remote_link=SVV_REMOTE_LINK, local_path=zip_path, auto_unzip=True
        )
