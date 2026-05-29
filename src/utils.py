from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd


def parse_time(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return pd.to_datetime(value).to_pydatetime()


def minutes_between(start, end) -> float:
    start_dt = parse_time(start)
    end_dt = parse_time(end)
    return (end_dt - start_dt).total_seconds() / 60.0


def add_minutes(value, minutes: float) -> datetime:
    return parse_time(value) + timedelta(minutes=float(minutes))


def read_table(path: Path) -> pd.DataFrame:
    path = Path(path)
    if path.exists() and path.suffix.lower() == '.parquet':
        try:
            return pd.read_parquet(path)
        except Exception:
            csv_fallback = path.with_suffix('.csv')
            if csv_fallback.exists():
                return pd.read_csv(csv_fallback)
            raise
    if path.exists() and path.suffix.lower() == '.csv':
        return pd.read_csv(path)
    if path.suffix.lower() == '.parquet':
        csv_fallback = path.with_suffix('.csv')
        if csv_fallback.exists():
            return pd.read_csv(csv_fallback)
    if path.suffix.lower() in {'.xlsx', '.xls'}:
        return pd.read_excel(path)
    raise FileNotFoundError(f'File not found or unsupported type: {path}')


def save_table(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == '.parquet':
        try:
            df.to_parquet(path, index=False)
            return
        except Exception:
            df.to_csv(path.with_suffix('.csv'), index=False)
            return
    if path.suffix.lower() == '.csv':
        df.to_csv(path, index=False)
        return
    raise ValueError(f'Unsupported output type: {path.suffix}')
