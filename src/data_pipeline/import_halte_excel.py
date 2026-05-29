from __future__ import annotations

"""Import and normalize Transjakarta stop data from an Excel file.

The hackathon prototype can run with generated demo data, but this script lets the
team include the provided halte spreadsheet as an additional stop reference.

Usage:
    python -m src.data_pipeline.import_halte_excel --path data/raw/Daftar_Halte_BRT_Transjakarta_31_Rute_revisi.xlsx
"""

import argparse
import re
from pathlib import Path

import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR


def _normalize_column_name(name: str) -> str:
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def _first_existing(columns: list[str], candidates: list[str]) -> str | None:
    colset = set(columns)
    for c in candidates:
        if c in colset:
            return c
    return None


def import_halte_excel(path: str | Path, output_name: str = "halte_transjakarta_normalized.csv") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path)
    df.columns = [_normalize_column_name(c) for c in df.columns]

    stop_id_col = _first_existing(df.columns.tolist(), ["stop_id", "id_halte", "kode_halte", "id", "no"])
    stop_name_col = _first_existing(df.columns.tolist(), ["stop_name", "nama_halte", "halte", "nama", "nama_stop"])
    lat_col = _first_existing(df.columns.tolist(), ["lat", "latitude", "y"])
    lon_col = _first_existing(df.columns.tolist(), ["lon", "lng", "longitude", "x"])
    route_col = _first_existing(df.columns.tolist(), ["route_id", "rute", "koridor", "corridor", "trayek"])

    out = pd.DataFrame()
    out["stop_id"] = df[stop_id_col].astype(str) if stop_id_col else [f"TJ_EXCEL_{i+1:04d}" for i in range(len(df))]
    out["stop_name"] = df[stop_name_col].astype(str) if stop_name_col else out["stop_id"]
    out["lat"] = pd.to_numeric(df[lat_col], errors="coerce") if lat_col else None
    out["lon"] = pd.to_numeric(df[lon_col], errors="coerce") if lon_col else None
    out["route_id"] = df[route_col].astype(str) if route_col else "UNKNOWN"
    out["source_file"] = path.name

    out = out.drop_duplicates(subset=["stop_id", "stop_name"]).reset_index(drop=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / output_name
    out.to_csv(output_path, index=False)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=str(RAW_DIR / "Daftar_Halte_BRT_Transjakarta_31_Rute_revisi.xlsx"))
    args = parser.parse_args()
    out = import_halte_excel(args.path)
    print(f"Imported {len(out)} stops into {PROCESSED_DIR / 'halte_transjakarta_normalized.csv'}")


if __name__ == "__main__":
    main()
