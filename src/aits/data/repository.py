from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import pandas as pd

from src.aits.config import RAW_DIR


def _read_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}. Run `python scripts/bootstrap_demo.py` first.")
    return pd.read_csv(path, parse_dates=parse_dates)


@lru_cache(maxsize=32)
def stops() -> pd.DataFrame:
    return _read_csv("stops.csv")


@lru_cache(maxsize=32)
def routes() -> pd.DataFrame:
    return _read_csv("routes.csv")


@lru_cache(maxsize=32)
def transfer_nodes() -> pd.DataFrame:
    return _read_csv("transfer_nodes.csv")


@lru_cache(maxsize=32)
def user_profiles() -> pd.DataFrame:
    return _read_csv("user_profiles.csv")


@lru_cache(maxsize=32)
def rail_schedule() -> pd.DataFrame:
    return _read_csv("rail_schedule.csv", parse_dates=["departure_time"])


@lru_cache(maxsize=32)
def non_rail_schedule() -> pd.DataFrame:
    return _read_csv("non_rail_schedule.csv", parse_dates=["scheduled_arrival"])


@lru_cache(maxsize=32)
def incidents() -> pd.DataFrame:
    return _read_csv("incidents.csv", parse_dates=["timestamp"])


def clear_cache() -> None:
    stops.cache_clear()
    routes.cache_clear()
    transfer_nodes.cache_clear()
    user_profiles.cache_clear()
    rail_schedule.cache_clear()
    non_rail_schedule.cache_clear()
    incidents.cache_clear()
