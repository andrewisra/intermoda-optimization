from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = ROOT_DIR / "models"

WAITING_TIME_TARGET_MINUTES = 8.0
MAX_HOLD_MINUTES = 3.0
MAX_SAFE_SPEED_KMH = 50.0
MIN_SAFE_SPEED_KMH = 5.0

RAIL_MODES = {"MRT", "LRT", "KRL"}
NON_RAIL_MODES = {"TRANSJAKARTA", "MIKROTRANS", "FEEDER", "SCHOOL_BUS"}

WALKING_CATEGORY_DEFAULTS = {
    "VERY_SHORT": {"min": 1, "max": 5, "default": 4},
    "SHORT": {"min": 6, "max": 10, "default": 8},
    "MEDIUM": {"min": 11, "max": 15, "default": 13},
    "LONG": {"min": 16, "max": 20, "default": 18},
    "VERY_LONG": {"min": 21, "max": 30, "default": 23},
}

USER_WALKING_PROFILES = {
    "FAST": 0.85,
    "STANDARD": 1.00,
    "RELAXED": 1.25,
    "ASSISTED": 1.50,
}
