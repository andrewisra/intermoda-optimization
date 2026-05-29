from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from src.aits.config import MODEL_DIR


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


class ModelRegistry:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = model_dir
        self._eta_model = None
        self._density_model = None

    @property
    def eta_model(self):
        if self._eta_model is None:
            path = self.model_dir / "eta_delay_model.joblib"
            if not path.exists():
                raise FileNotFoundError("ETA model not found. Run `python scripts/train_models.py` first.")
            self._eta_model = joblib.load(path)
        return self._eta_model

    @property
    def density_model(self):
        if self._density_model is None:
            path = self.model_dir / "density_model.joblib"
            if not path.exists():
                raise FileNotFoundError("Density model not found. Run `python scripts/train_models.py` first.")
            self._density_model = joblib.load(path)
        return self._density_model

    def predict_eta_delay(self, features: dict) -> EtaPrediction:
        row = pd.DataFrame([features])
        delay = float(max(0.0, self.eta_model.predict(row)[0]))
        scheduled = float(features.get("scheduled_travel_minutes", 0.0))
        eta = scheduled + delay
        # Heuristic confidence: lower when incidents/traffic/rain are high.
        risk = 0.06 * float(features.get("traffic_level", 0)) + 0.05 * float(features.get("rainfall_level", 0)) + 0.18 * float(features.get("incident_flag", 0))
        confidence = float(np.clip(0.93 - risk, 0.45, 0.95))
        return EtaPrediction(round(delay, 2), round(eta, 2), round(confidence, 2))

    def predict_density(self, features: dict) -> DensityPrediction:
        row = pd.DataFrame([features])
        model = self.density_model
        label = str(model.predict(row)[0])
        confidence = 0.75
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(row)[0]
            confidence = float(np.max(proba))
        load_factor = float(features.get("tap_in_count_15m", 0)) / max(float(features.get("vehicle_capacity", 1)), 1.0)
        return DensityPrediction(label, round(load_factor, 2), round(float(confidence), 2))


registry = ModelRegistry()
