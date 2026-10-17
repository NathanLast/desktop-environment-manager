from typing import TextIO, Literal, Iterator
from pathlib import Path
import shutil


class StorageHandler:
    def __init__(self, base: Path):
        self._base = base
        self.assert_directory_exists()
        if not self._base.is_dir():
            raise ValueError("StorageHandler should only handle directories")

    def sub_handler(self, rel_path: Path | str) -> "StorageHandler":
        full_sub_path = self.get_full_path(rel_path=rel_path)
        return StorageHandler(full_sub_path)

    def scan_dir(self) -> Iterator["StorageHandler"]:
        for entry in self._base.iterdir():
            if entry.is_dir():
                yield StorageHandler(entry)

    def open_relative(self, rel_path: Path, mode: Literal["r", "w"]) -> TextIO:
        full_path = self.get_full_path(rel_path)
        if full_path.is_dir():
            raise IsADirectoryError(f"Cannot open directory as file: {rel_path}")
        self.assert_file_exists(rel_path)
        return open(full_path, mode)

    def delete_relative(self, rel_path: Path | str = Path()) -> None:
        full_path = self.get_full_path(rel_path)
        if full_path.is_dir():
            shutil.rmtree(full_path, ignore_errors=True)
        else:
            full_path.unlink(missing_ok=True)

    def assert_file_exists(self, rel_path: Path) -> None:
        path = self.get_full_path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def assert_directory_exists(self, rel_path: Path = Path()) -> None:
        path = self.get_full_path(rel_path)
        path.mkdir(parents=True, exist_ok=True)

    def get_full_path(self, rel_path: Path | str = Path()) -> Path:
        if isinstance(rel_path, str):
            rel_path = Path(rel_path)
        return self._base / rel_path
