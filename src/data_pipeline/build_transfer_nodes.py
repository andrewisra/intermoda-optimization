from __future__ import annotations
import pandas as pd
from src.config import RAW_DIR, PROCESSED_DIR


def build_transfer_nodes(input_csv: str | None = None) -> pd.DataFrame:
    if input_csv:
        df = pd.read_csv(input_csv)
    else:
        path = RAW_DIR / "transfer_nodes.csv"
        if path.exists():
            df = pd.read_csv(path)
        else:
            df = pd.DataFrame([
                {"from_stop_id":"TJ_DUKUH_ATAS","to_stop_id":"MRT_DUKUH_ATAS","walking_time_minutes":6,"category":"medium"},
                {"from_stop_id":"TJ_DUKUH_ATAS","to_stop_id":"KRL_SUDIRMAN","walking_time_minutes":9,"category":"medium"},
            ])
    required = {"from_stop_id", "to_stop_id", "walking_time_minutes"}
    if not required.issubset(df.columns):
        raise ValueError(f"transfer_nodes wajib punya kolom {required}")
    try:
        df.to_parquet(PROCESSED_DIR / "transfer_nodes.parquet", index=False)
    except Exception:
        df.to_csv(PROCESSED_DIR / "transfer_nodes.csv", index=False)
    return df


if __name__ == "__main__":
    print(build_transfer_nodes())
