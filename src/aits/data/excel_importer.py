from __future__ import annotations

from pathlib import Path
import pandas as pd


def import_transjakarta_halte_excel(excel_path: str | Path, output_csv: str | Path) -> pd.DataFrame:
    """Import file Excel daftar halte dari user jika tersedia.

    Fungsi ini dibuat fleksibel karena format kolom Excel dapat berbeda-beda.
    Sistem akan mencoba mencari kolom yang mirip nama halte, latitude, longitude, dan rute.
    """
    excel_path = Path(excel_path)
    output_csv = Path(output_csv)
    df = pd.read_excel(excel_path)
    normalized = {str(col).strip().lower(): col for col in df.columns}

    def find_col(candidates: list[str]):
        for key, original in normalized.items():
            if any(c in key for c in candidates):
                return original
        return None

    name_col = find_col(["halte", "stop", "nama"])
    lat_col = find_col(["lat", "latitude"])
    lon_col = find_col(["lon", "lng", "longitude"])
    route_col = find_col(["rute", "route", "koridor"])

    out = pd.DataFrame()
    if name_col:
        out["stop_name"] = df[name_col].astype(str)
    else:
        out["stop_name"] = [f"Stop {i+1}" for i in range(len(df))]

    out["stop_id"] = out["stop_name"].str.upper().str.replace(r"[^A-Z0-9]+", "_", regex=True).str.strip("_")
    out["mode"] = "TRANSJAKARTA"
    out["lat"] = df[lat_col] if lat_col else None
    out["lon"] = df[lon_col] if lon_col else None
    out["route_hint"] = df[route_col] if route_col else None

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False)
    return out
