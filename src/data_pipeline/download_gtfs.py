from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import requests

from src.config import RAW_DIR

GTFS_URL = "https://gtfs.transjakarta.co.id/files/file_gtfs.zip"
GTFS_DIR = RAW_DIR / "gtfs_transjakarta"
EXPECTED_FILES = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
CHECKSUM_FILE = GTFS_DIR / ".gtfs_checksum"


def _compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_gtfs(url: str = GTFS_URL, force: bool = False, offline: bool = False) -> Path:
    """Download and extract the Transjakarta GTFS feed.

    Args:
        url: URL to download the GTFS ZIP from.
        force: Re-download even if the directory already exists.
        offline: Skip download if files already exist; raise if missing.

    Returns:
        Path to the extracted GTFS directory.
    """
    GTFS_DIR.mkdir(parents=True, exist_ok=True)

    already_extracted = all((GTFS_DIR / f).exists() for f in EXPECTED_FILES)

    if already_extracted and not force:
        print(f"GTFS already present at {GTFS_DIR} ({len(list(GTFS_DIR.iterdir()))} files). Skipping download.")
        return GTFS_DIR

    if offline:
        if already_extracted:
            return GTFS_DIR
        raise FileNotFoundError(
            f"GTFS files not found in {GTFS_DIR} and --offline flag is set. "
            "Run without --offline to download."
        )

    print(f"Downloading GTFS from {url} ...")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        if already_extracted:
            print(f"Download failed ({e}), but existing GTFS files found. Continuing with local copy.")
            return GTFS_DIR
        raise RuntimeError(f"Failed to download GTFS and no local copy exists: {e}") from e

    zip_path = RAW_DIR / "gtfs_transjakarta.zip"
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded {zip_path.stat().st_size / 1024:.0f} KB to {zip_path}")

    print(f"Extracting to {GTFS_DIR} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(GTFS_DIR)

    missing = [f for f in EXPECTED_FILES if not (GTFS_DIR / f).exists()]
    if missing:
        raise RuntimeError(f"GTFS ZIP is incomplete. Missing files: {missing}")

    checksum = _compute_file_hash(zip_path)
    CHECKSUM_FILE.write_text(checksum)
    print(f"GTFS extracted successfully. Checksum: {checksum[:16]}...")

    return GTFS_DIR


def get_gtfs_path() -> Path:
    """Return the path to the GTFS directory, raising if not found."""
    if GTFS_DIR.exists() and all((GTFS_DIR / f).exists() for f in EXPECTED_FILES):
        return GTFS_DIR
    raise FileNotFoundError(
        f"GTFS not found at {GTFS_DIR}. Run: python -m src.data_pipeline.download_gtfs"
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Download Transjakarta GTFS feed")
    parser.add_argument("--force", action="store_true", help="Re-download even if files exist")
    parser.add_argument("--offline", action="store_true", help="Use local files only, do not download")
    parser.add_argument("--url", default=GTFS_URL, help="Custom GTFS ZIP URL")
    args = parser.parse_args()

    path = download_gtfs(url=args.url, force=args.force, offline=args.offline)
    print(f"GTFS ready at: {path}")
    print(f"Files: {sorted(f.name for f in path.iterdir() if f.suffix == '.txt')}")


if __name__ == "__main__":
    main()
