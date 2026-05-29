from __future__ import annotations

import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from src.config import PROCESSED_DIR
from src.utils import read_table

MODEL_PATH = PROCESSED_DIR / 'eta_delay_model.pkl'


def _read_processed_stop_times() -> pd.DataFrame:
    for name in ['stop_times', 'schedules']:
        for suffix in ['.parquet', '.csv']:
            path = PROCESSED_DIR / f'{name}{suffix}'
            if path.exists():
                return read_table(path)
    raise FileNotFoundError('Processed stop_times/schedules dataset not found. Run python scripts/bootstrap_demo.py first.')


def build_training_table() -> pd.DataFrame:
    df = _read_processed_stop_times()
    df['arrival_time'] = pd.to_datetime(df['arrival_time'])
    rng = np.random.default_rng(42)
    out = df[['route_id', 'stop_id', 'stop_sequence', 'arrival_time', 'mode']].copy()
    out['hour'] = out['arrival_time'].dt.hour
    out['dayofweek'] = out['arrival_time'].dt.dayofweek
    out['is_peak'] = out['hour'].isin([7, 8, 17, 18, 19]).astype(int)
    out['rain_flag'] = rng.integers(0, 2, len(out))
    out['incident_flag'] = rng.choice([0, 1], size=len(out), p=[0.85, 0.15])
    out['delay_minutes'] = (
        rng.normal(loc=1.5, scale=0.8, size=len(out)).clip(0, 8)
        + out['is_peak'] * rng.uniform(1.0, 3.0, len(out))
        + out['rain_flag'] * rng.uniform(0.5, 2.0, len(out))
        + out['incident_flag'] * rng.uniform(3.0, 8.0, len(out))
    ).round(2)
    return out


def train_model() -> dict:
    df = build_training_table()
    features = ['stop_sequence', 'hour', 'dayofweek', 'is_peak', 'rain_flag', 'incident_flag']
    X = df[features]
    y = df['delay_minutes']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestRegressor(n_estimators=120, random_state=42, min_samples_leaf=2)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    payload = {'model': model, 'features': features, 'mae_minutes': mae}
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(payload, f)
    return {'model_path': str(MODEL_PATH), 'mae_minutes': round(mae, 3), 'rows': len(df)}


def predict_delay(stop_sequence: int, hour: int, dayofweek: int, is_peak: int, rain_flag: int, incident_flag: int) -> float:
    if not MODEL_PATH.exists():
        train_model()
    with open(MODEL_PATH, 'rb') as f:
        payload = pickle.load(f)
    X = pd.DataFrame([{
        'stop_sequence': stop_sequence,
        'hour': hour,
        'dayofweek': dayofweek,
        'is_peak': is_peak,
        'rain_flag': rain_flag,
        'incident_flag': incident_flag,
    }])[payload['features']]
    return float(payload['model'].predict(X)[0])


if __name__ == '__main__':
    print(train_model())
