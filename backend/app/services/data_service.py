from __future__ import annotations
from pathlib import Path
import subprocess
import sys
import pandas as pd
from src.config import PROCESSED_DIR, ROOT_DIR


def ensure_demo_data() -> None:
    if not (PROCESSED_DIR / "schedules.parquet").exists() and not (PROCESSED_DIR / "schedules.csv").exists():
        subprocess.run([sys.executable, "-m", "src.data_pipeline.generate_demo_data"], cwd=ROOT_DIR, check=True)


def load_processed(name: str) -> pd.DataFrame:
    ensure_demo_data()
    parquet_path = PROCESSED_DIR / f"{name}.parquet"
    csv_path = PROCESSED_DIR / f"{name}.csv"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    if csv_path.exists():
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"Processed data not found: {parquet_path} or {csv_path}")
