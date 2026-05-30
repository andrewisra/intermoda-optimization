from __future__ import annotations

from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.aits.config import RAW_DIR, MODEL_DIR


def train_eta_model() -> dict:
    df = pd.read_csv(RAW_DIR / "training_eta.csv")
    target = "delay_minutes"
    categorical = ["route_id", "stop_id"]
    numeric = ["hour", "day_of_week", "traffic_level", "rainfall_level", "incident_flag", "passenger_density_score", "scheduled_travel_minutes"]
    X = df[categorical + numeric]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("num", StandardScaler(), numeric),
    ])
    model = RandomForestRegressor(n_estimators=220, random_state=42, min_samples_leaf=3, n_jobs=-1)
    pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    metrics = {"mae_minutes": round(float(mean_absolute_error(y_test, pred)), 3), "rows": int(len(df))}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_DIR / "eta_delay_model.joblib")
    return metrics


def train_density_model() -> dict:
    df = pd.read_csv(RAW_DIR / "training_density.csv")
    target = "density_level"
    categorical = ["stop_id", "route_id"]
    numeric = ["hour", "day_of_week", "tap_in_count_15m", "scheduled_headway_minutes", "vehicle_capacity", "event_flag", "rainfall_level"]
    X = df[categorical + numeric]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("num", StandardScaler(), numeric),
    ])
    model = RandomForestClassifier(n_estimators=220, random_state=42, min_samples_leaf=3, class_weight="balanced", n_jobs=-1)
    pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    metrics = {"accuracy": round(float(accuracy_score(y_test, pred)), 3), "rows": int(len(df))}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_DIR / "density_model.joblib")
    return metrics


def train_all() -> dict:
    metrics = {"eta": train_eta_model(), "density": train_density_model()}
    with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train_all()
