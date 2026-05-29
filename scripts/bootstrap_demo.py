from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap demo data and train ETA model")
    parser.add_argument("--skip-gtfs", action="store_true", help="Skip GTFS download and parsing")
    parser.add_argument("--gtfs-only", action="store_true", help="Only download and parse GTFS, skip synthetic data")
    parser.add_argument("--offline", action="store_true", help="Use local GTFS files only, do not download")
    parser.add_argument("--force-download", action="store_true", help="Force re-download of GTFS")
    parser.add_argument("--auto-transfers", action="store_true", help="Auto-generate transfer nodes from GTFS proximity (slow for large feeds)")
    args = parser.parse_args()

    if not args.skip_gtfs:
        try:
            from src.data_pipeline.download_gtfs import download_gtfs
            from src.data_pipeline.parse_gtfs import parse_gtfs
            from src.config import PROCESSED_DIR

            print("=" * 60)
            print("Step 1: Downloading Transjakarta GTFS feed")
            print("=" * 60)
            try:
                gtfs_path = download_gtfs(force=args.force_download, offline=args.offline)
            except Exception as e:
                print(f"GTFS download failed: {e}")
                print("Continuing with synthetic data only.")
                gtfs_path = None

            if gtfs_path is not None:
                print(f"\nGTFS downloaded to: {gtfs_path}")
                print("=" * 60)
                print("Step 2: Parsing GTFS files")
                print("=" * 60)
                frames = parse_gtfs(gtfs_path)
                for k, v in frames.items():
                    print(f"  {k}: {len(v)} rows")

                if args.auto_transfers:
                    from src.data_pipeline.parse_gtfs import build_transfer_nodes_from_gtfs
                    from src.utils import save_table
                    print("\nAuto-generating transfer nodes from GTFS proximity...")
                    transfers = build_transfer_nodes_from_gtfs(gtfs_path)
                    print(f"  transfer_nodes: {len(transfers)} rows")
                    try:
                        save_table(transfers, PROCESSED_DIR / "transfer_nodes.parquet")
                    except Exception:
                        transfers.to_csv(PROCESSED_DIR / "transfer_nodes.csv", index=False)
                    print("  Saved to data/processed/transfer_nodes.parquet")
        except ImportError as e:
            print(f"Could not import GTFS modules: {e}")
            print("Continuing with synthetic data only.")
        except Exception as e:
            print(f"GTFS pipeline error: {e}")
            print("Continuing with synthetic data only.")

    if not args.gtfs_only:
        print("\n" + "=" * 60)
        print("Step 3: Generating synthetic demo data")
        print("=" * 60)
        try:
            from src.data_pipeline.generate_demo_data import main as generate_sample_data
        except ImportError:
            from src.data_pipeline.generate_sample_data import main as generate_sample_data
        generate_sample_data()

        print("\n" + "=" * 60)
        print("Step 4: Training ETA model")
        print("=" * 60)
        from src.eta.train_eta_model import train_model
        result = train_model()
        print(f"ETA model trained: {result}")

    print("\n" + "=" * 60)
    print("Bootstrap complete!")
    print("=" * 60)
    print("Next steps:")
    print("  1) make api        - Start the FastAPI backend")
    print("  2) make dashboard  - Start the Streamlit dashboard")


if __name__ == "__main__":
    main()
