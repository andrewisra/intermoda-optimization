from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", DATA_DIR / "processed"))

MAX_WAITING_MINUTES = float(os.getenv("MAX_WAITING_MINUTES", 8))
MAX_DWELL_EXTENSION_MINUTES = float(os.getenv("MAX_DWELL_EXTENSION_MINUTES", 3))
MAX_SAFE_SPEED_KMH = float(os.getenv("MAX_SAFE_SPEED_KMH", 50))
MIN_SAFE_SPEED_KMH = float(os.getenv("MIN_SAFE_SPEED_KMH", 10))

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
