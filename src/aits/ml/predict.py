"""predict.py v2 — Inference pipeline for ETA (XGBoost) and Density (CatBoost) models.

Architecture:
  FeatureBuilder  →  builds raw feature DataFrame matching training schema
  ModelRegistry   →  lazy-loads models, runs inference

ETA model: sklearn Pipeline([ColumnTransformer, XGBRegressor]) saved as .joblib
Density model: native CatBoostClassifier saved as .cbm + LabelEncoder .joblib
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.aits.config import MODEL_DIR, RAW_DIR

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EtaPrediction:
    predicted_delay_minutes: float
    predicted_eta_minutes: float
    confidence_score: float


@dataclass
class DensityPrediction:
    density_level: str
    load_factor_estimate: float
    confidence_score: float


# ---------------------------------------------------------------------------
# GTFS lookups — computed once, cached for inference
# ---------------------------------------------------------------------------

_RUSH_MORNING = set(range(7, 10))
_RUSH_EVENING = set(range(16, 20))


def _load_gtfs_connectivity() -> dict[str, int]:
    """Count routes per stop from GTFS."""
    gtfs_dir = RAW_DIR / "gtfs_transjakarta"
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", low_memory=False)
    trips = pd.read_csv(gtfs_dir / "trips.txt", low_memory=False)
    merged = stop_times[["trip_id", "stop_id"]].merge(
        trips[["trip_id", "route_id"]], on="trip_id"
    )
    return merged.groupby("stop_id")["route_id"].nunique().to_dict()


def _load_gtfs_terminals() -> set[str]:
    """Identify terminal stops (first/last stop of any trip)."""
    gtfs_dir = RAW_DIR / "gtfs_transjakarta"
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", low_memory=False)
    terminals = set()
    for _, group in stop_times.groupby("trip_id"):
        seq = group.sort_values("stop_sequence")
        terminals.add(seq.iloc[0]["stop_id"])
        terminals.add(seq.iloc[-1]["stop_id"])
    return terminals


def _load_gtfs_route_factors() -> dict[str, float]:
    """Per-route demand factor from headway (0.8-1.2)."""
    gtfs_dir = RAW_DIR / "gtfs_transjakarta"
    trips = pd.read_csv(gtfs_dir / "trips.txt", low_memory=False)
    freq_path = gtfs_dir / "frequencies.txt"

    if freq_path.exists():
        freq = pd.read_csv(freq_path)
        freq_r = freq.merge(trips[["trip_id", "route_id"]].drop_duplicates(), on="trip_id")
        route_headway = freq_r.groupby("route_id")["headway_secs"].mean() / 60.0
    else:
        route_trips = trips.groupby("route_id").size()
        route_headway = 60.0 / route_trips.clip(lower=1)

    min_h, max_h = route_headway.min(), route_headway.max()
    if max_h > min_h:
        norm = (route_headway - min_h) / (max_h - min_h)
    else:
        norm = pd.Series(0.5, index=route_headway.index)
    return (0.8 + 0.4 * norm).to_dict()


# ---------------------------------------------------------------------------
# FeatureBuilder — raw dict → DataFrame matching training schema
# ---------------------------------------------------------------------------

# Feature lists must match train.py exactly
_ETA_CAT_FEATURES = ["route_id", "from_stop_id", "to_stop_id", "route_mode"]
_ETA_NUM_FEATURES = [
    "scheduled_travel_seconds", "headway_minutes",
    "rainfall_level", "flood_flag", "temperature_c",
    "historical_incident_rate", "is_rush_hour",
]

_DENSITY_CAT_FEATURES = ["from_stop_id", "route_id"]
_DENSITY_NUM_FEATURES = [
    "headway_minutes", "vehicle_capacity",
    "hour", "day_of_week", "is_rush_hour",
    "rainfall_level", "flood_flag", "event_flag",
    "routes_through_stop", "is_terminal", "route_demand_factor",
]


class FeatureBuilder:
    """Builds inference-time feature DataFrames matching the training schema."""

    def __init__(self):
        # Lazy-loaded GTFS lookups
        self._connectivity: dict[str, int] | None = None
        self._terminals: set[str] | None = None
        self._route_factors: dict[str, float] | None = None

    def _ensure_gtfs_lookups(self):
        if self._connectivity is None:
            try:
                self._connectivity = _load_gtfs_connectivity()
                self._terminals = _load_gtfs_terminals()
                self._route_factors = _load_gtfs_route_factors()
            except Exception as e:
                log.warning("Failed to load GTFS lookups: %s — using defaults", e)
                self._connectivity = {}
                self._terminals = set()
                self._route_factors = {}

    def build_eta_features(
        self,
        *,
        route_id: str,
        from_stop_id: str,
        to_stop_id: str,
        route_mode: str,
        scheduled_travel_seconds: int,
        headway_minutes: float,
        hour: int,
        day_of_week: int,
        rainfall_level: int = 0,
        flood_flag: int = 0,
        temperature_c: int = 28,
        historical_incident_rate: float = 0.0,
    ) -> pd.DataFrame:
        """Build one-row DataFrame with all ETA features + cyclical encoding."""
        is_rush = 1 if (hour in _RUSH_MORNING or hour in _RUSH_EVENING) else 0
        row = {
            "route_id": route_id,
            "from_stop_id": from_stop_id,
            "to_stop_id": to_stop_id,
            "route_mode": route_mode,
            "scheduled_travel_seconds": int(scheduled_travel_seconds),
            "headway_minutes": float(headway_minutes),
            "rainfall_level": int(rainfall_level),
            "flood_flag": int(flood_flag),
            "temperature_c": int(temperature_c),
            "historical_incident_rate": float(historical_incident_rate),
            "is_rush_hour": is_rush,
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "dow_sin": math.sin(2 * math.pi * day_of_week / 7),
            "dow_cos": math.cos(2 * math.pi * day_of_week / 7),
        }
        return pd.DataFrame([row])

    def build_density_features(
        self,
        *,
        from_stop_id: str,
        route_id: str,
        headway_minutes: float,
        vehicle_capacity: int,
        hour: int,
        day_of_week: int,
        rainfall_level: int = 0,
        flood_flag: int = 0,
        event_flag: int = 0,
        routes_through_stop: int | None = None,
        is_terminal: int | None = None,
        route_demand_factor: float | None = None,
    ) -> pd.DataFrame:
        """Build one-row DataFrame with all density features.

        The 3 new features (routes_through_stop, is_terminal, route_demand_factor)
        are auto-computed from GTFS data when not explicitly provided.
        """
        self._ensure_gtfs_lookups()
        is_rush = 1 if (hour in _RUSH_MORNING or hour in _RUSH_EVENING) else 0

        if routes_through_stop is None:
            routes_through_stop = self._connectivity.get(from_stop_id, 1)
        if is_terminal is None:
            is_terminal = 1 if from_stop_id in self._terminals else 0
        if route_demand_factor is None:
            route_demand_factor = self._route_factors.get(route_id, 1.0)

        row = {
            "from_stop_id": from_stop_id,
            "route_id": route_id,
            "headway_minutes": float(headway_minutes),
            "vehicle_capacity": int(vehicle_capacity),
            "hour": int(hour),
            "day_of_week": int(day_of_week),
            "is_rush_hour": is_rush,
            "rainfall_level": int(rainfall_level),
            "flood_flag": int(flood_flag),
            "event_flag": int(event_flag),
            "routes_through_stop": int(routes_through_stop),
            "is_terminal": int(is_terminal),
            "route_demand_factor": float(route_demand_factor),
        }
        return pd.DataFrame([row])


# ---------------------------------------------------------------------------
# ModelRegistry — lazy-loading model inference
# ---------------------------------------------------------------------------

class ModelRegistry:
    def __init__(
        self,
        model_dir: Path = MODEL_DIR,
        density_label_encoder_path: Path | None = None,
    ):
        self.model_dir = model_dir
        self._density_label_encoder_path = density_label_encoder_path
        self._eta_pipeline = None
        self._density_model = None
        self._density_label_encoder = None
        self._feature_builder = FeatureBuilder()

    # -- lazy loaders -------------------------------------------------------

    @property
    def eta_pipeline(self):
        if self._eta_pipeline is None:
            path = self.model_dir / "eta_xgb_model.joblib"
            if not path.exists():
                raise FileNotFoundError(
                    "ETA model not found at %s. Run `python scripts/train_eta.py` first." % path
                )
            self._eta_pipeline = joblib.load(path)
        return self._eta_pipeline

    @property
    def density_model(self):
        """Load CatBoost density model (.cbm format)."""
        if self._density_model is None:
            cbm_path = self.model_dir / "density_catboost_model.cbm"
            xgb_path = self.model_dir / "density_xgb_model.joblib"

            if cbm_path.exists():
                from catboost import CatBoostClassifier
                model = CatBoostClassifier()
                model.load_model(str(cbm_path))
                self._density_model = ("catboost", model)
                log.info("Loaded CatBoost density model from %s", cbm_path)
            elif xgb_path.exists():
                self._density_model = ("sklearn_pipeline", joblib.load(xgb_path))
                log.info("Loaded sklearn density pipeline from %s (legacy)", xgb_path)
            else:
                raise FileNotFoundError(
                    "Density model not found. Run `python scripts/train_density.py` first."
                )
        return self._density_model

    @property
    def density_label_encoder(self):
        if self._density_label_encoder is None:
            path = self._density_label_encoder_path or (self.model_dir / "density_label_encoder.joblib")
            if not path.exists():
                raise FileNotFoundError(
                    "Density label encoder not found at %s." % path
                )
            self._density_label_encoder = joblib.load(path)
        return self._density_label_encoder

    # -- prediction ---------------------------------------------------------

    def predict_eta_delay(self, features: dict) -> EtaPrediction:
        """Predict ETA delay using XGBoost Pipeline."""
        df = self._feature_builder.build_eta_features(**features)
        raw_pred = float(self.eta_pipeline.predict(df)[0])
        delay = max(0.0, raw_pred)
        scheduled_min = float(features.get("scheduled_travel_seconds", 0)) / 60.0
        eta = scheduled_min + delay

        risk = (
            0.06 * float(features.get("rainfall_level", 0))
            + 0.05 * float(features.get("flood_flag", 0))
            + 0.18 * float(features.get("historical_incident_rate", 0))
        )
        confidence = float(np.clip(0.93 - risk, 0.45, 0.95))

        return EtaPrediction(
            predicted_delay_minutes=round(delay, 2),
            predicted_eta_minutes=round(eta, 2),
            confidence_score=round(confidence, 2),
        )

    def predict_density(self, features: dict) -> DensityPrediction:
        """Predict passenger density.

        Supports both CatBoost (.cbm) and legacy sklearn pipeline models.
        Falls back to MEDIUM/0.0 confidence when the density model is not available.
        """
        try:
            model_type, model = self.density_model
            le = self.density_label_encoder
        except FileNotFoundError:
            log.warning("Density model unavailable — returning default MEDIUM prediction")
            load_factor = float(features.get("vehicle_capacity", 80))
            return DensityPrediction(
                density_level="MEDIUM",
                load_factor_estimate=round(load_factor, 2),
                confidence_score=0.0,
            )

        df = self._feature_builder.build_density_features(**features)

        if model_type == "catboost":
            from catboost import Pool
            pool = Pool(data=df, cat_features=_DENSITY_CAT_FEATURES)
            pred_encoded = int(model.predict(pool)[0])
            label = str(le.inverse_transform([pred_encoded])[0])

            confidence = 0.75
            try:
                proba = model.predict_proba(pool)[0]
                confidence = float(np.max(proba))
            except Exception:
                pass
        else:
            # Legacy sklearn pipeline
            pred_encoded = int(model.predict(df)[0])
            label = str(le.inverse_transform([pred_encoded])[0])

            confidence = 0.75
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(df)[0]
                confidence = float(np.max(proba))

        load_factor = float(features.get("vehicle_capacity", 80))
        return DensityPrediction(
            density_level=label,
            load_factor_estimate=round(load_factor, 2),
            confidence_score=round(float(confidence), 2),
        )


# ---------------------------------------------------------------------------
# Module-level singleton (backward compatible with services.py imports)
# ---------------------------------------------------------------------------

registry = ModelRegistry()
