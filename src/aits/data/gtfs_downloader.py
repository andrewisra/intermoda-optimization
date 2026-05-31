from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import requests

from src.aits.config import RAW_DIR

GTFS_URL = "https://gtfs.transjakarta.co.id/files/file_gtfs.zip"
GTFS_ZIP = RAW_DIR / "gtfs_transjakarta.zip"
GTFS_DIR = RAW_DIR / "gtfs_transjakarta"
EXPECTED_FILES = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
CHECKSUM_FILE = GTFS_DIR / ".gtfs_checksum"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def has_extracted_gtfs(gtfs_dir: Path = GTFS_DIR) -> bool:
    return gtfs_dir.exists() and all((gtfs_dir / name).exists() for name in EXPECTED_FILES)


def extract_gtfs(zip_path: Path = GTFS_ZIP, gtfs_dir: Path = GTFS_DIR) -> Path:
    if not zip_path.exists():
        raise FileNotFoundError(f"GTFS ZIP not found: {zip_path}")
    gtfs_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(gtfs_dir)
    missing = [name for name in EXPECTED_FILES if not (gtfs_dir / name).exists()]
    if missing:
        raise RuntimeError(f"GTFS ZIP is incomplete. Missing files: {missing}")
    CHECKSUM_FILE.write_text(_sha256(zip_path), encoding="utf-8")
    return gtfs_dir


def download_gtfs(url: str = GTFS_URL, force: bool = False, offline: bool = False) -> Path:
    """Download/extract the official Transjakarta GTFS feed.

    This clean AITS project keeps only one GTFS pipeline under src/aits/data.
    It can work offline when data/raw/gtfs_transjakarta.zip is already present.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GTFS_DIR.mkdir(parents=True, exist_ok=True)

    if has_extracted_gtfs() and not force:
        print(f"GTFS already extracted at {GTFS_DIR}")
        return GTFS_DIR

    if GTFS_ZIP.exists() and offline:
        print(f"Using local GTFS ZIP: {GTFS_ZIP}")
        return extract_gtfs(GTFS_ZIP, GTFS_DIR)

    if offline:
        raise FileNotFoundError(
            f"GTFS not found at {GTFS_DIR} or {GTFS_ZIP}. Disable --offline to download it."
        )

    print(f"Downloading GTFS from {url}")
    try:
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        with open(GTFS_ZIP, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as exc:
        if GTFS_ZIP.exists():
            print(f"Download failed, but local ZIP exists. Using local file. Error: {exc}")
            return extract_gtfs(GTFS_ZIP, GTFS_DIR)
        if has_extracted_gtfs():
            print(f"Download failed, but extracted GTFS exists. Error: {exc}")
            return GTFS_DIR
        raise RuntimeError(f"Failed to download GTFS and no local GTFS exists: {exc}") from exc

    print(f"Downloaded {GTFS_ZIP} ({GTFS_ZIP.stat().st_size / 1024:.0f} KB)")
    return extract_gtfs(GTFS_ZIP, GTFS_DIR)


def get_gtfs_path() -> Path:
    if has_extracted_gtfs():
        return GTFS_DIR
    if GTFS_ZIP.exists():
        return extract_gtfs(GTFS_ZIP, GTFS_DIR)
    raise FileNotFoundError("GTFS not found. Run `python scripts/bootstrap_demo.py --with-gtfs`.")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Download or extract Transjakarta GTFS data")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--url", default=GTFS_URL)
    args = parser.parse_args()

    path = download_gtfs(url=args.url, force=args.force, offline=args.offline)
    print(f"GTFS ready at {path}")


if __name__ == "__main__":
    main()
