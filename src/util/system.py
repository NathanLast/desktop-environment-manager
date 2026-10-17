import subprocess
from pathlib import Path
from threading import Thread


def run_command(exe_path: Path, args: list[str], off_thread: bool = False) -> None:
    if off_thread:
        thread = Thread(target=run_command, args=(exe_path, args))
        thread.start()
    else:
        subprocess.run([str(exe_path)] + args)
