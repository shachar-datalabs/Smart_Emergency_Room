from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://ftp.cdc.gov/pub/health_statistics/nchs/datasets/NHAMCS/ed2022.zip"
SHA256 = "a513693ed05b98bf94d2ff48b50de85afe48dd63cd7d43fb0930f914b18a9f25"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_nhamcs(destination: Path, force: bool = False) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "ed2022.zip"
    raw_file = destination / "ed2022"
    if not archive.exists() or force:
        temporary = archive.with_suffix(".zip.part")
        with urllib.request.urlopen(URL, timeout=120) as response, temporary.open("wb") as out:
            shutil.copyfileobj(response, out)
        temporary.replace(archive)
    actual = sha256(archive)
    if actual != SHA256:
        raise ValueError(f"NHAMCS archive checksum mismatch: {actual}")
    if not raw_file.exists() or force:
        with zipfile.ZipFile(archive) as bundle:
            if bundle.namelist() != ["ed2022"]:
                raise ValueError(f"Unexpected archive members: {bundle.namelist()}")
            bundle.extract("ed2022", destination)
    if raw_file.stat().st_size == 0:
        raise ValueError("Extracted NHAMCS file is empty")
    return raw_file
