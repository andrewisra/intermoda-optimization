from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aits.data.generate_demo_data import generate_all
from src.aits.data.gtfs_downloader import download_gtfs
from src.aits.data.gtfs_parser import parse_gtfs, build_transfer_nodes_from_gtfs


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap demo data for the clean AITS project")
    parser.add_argument("--with-gtfs", action="store_true", help="Also extract/download and parse Transjakarta GTFS")
    parser.add_argument("--offline", action="store_true", help="Use local GTFS ZIP only; do not download")
    parser.add_argument("--force-download", action="store_true", help="Force GTFS re-download/extract")
    parser.add_argument("--auto-transfers", action="store_true", help="Generate candidate transfer links from GTFS proximity")
    args = parser.parse_args()

    print("Generating AITS demo data...")
    generate_all()
    print("Demo data generated.")

    if args.with_gtfs:
        print("Preparing GTFS data...")
        gtfs_path = download_gtfs(force=args.force_download, offline=args.offline)
        parse_gtfs(gtfs_path)
        if args.auto_transfers:
            transfers = build_transfer_nodes_from_gtfs(gtfs_path)
            print(f"Generated {len(transfers)} GTFS transfer candidate links.")
        print("GTFS pipeline completed.")


if __name__ == "__main__":
    main()
