import urllib.request
import zipfile
from pathlib import Path


def download_zip(remote_link: str, local_path: Path, auto_unzip: bool = False) -> None:
    """download a zip file from a remote link to a local path.
    if auto_unzip is True, the zip file will be extracted in-place
     keeping its name"""
    # download the zip file
    urllib.request.urlretrieve(remote_link, local_path)

    if auto_unzip:
        # Extract the zip in-place keeping its name
        extract_dir = local_path.with_suffix("")
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(local_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
