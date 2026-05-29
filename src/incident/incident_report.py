from __future__ import annotations

from datetime import datetime
import uuid
import pandas as pd

from src.config import PROCESSED_DIR
from src.utils import save_table, read_table


def load_incidents() -> pd.DataFrame:
    path = PROCESSED_DIR / 'incidents.parquet'
    if path.exists() or path.with_suffix('.csv').exists():
        return read_table(path)
    return pd.DataFrame(columns=['incident_id','type','severity','route_id','stop_id','lat','lon','delay_impact_minutes','description','status','reported_at'])


def report_incident(incident_type: str, severity: str, route_id: str, stop_id: str, lat: float, lon: float, delay_impact_minutes: float, description: str = '') -> dict:
    df = load_incidents()
    row = {'incident_id': 'INC_' + uuid.uuid4().hex[:8].upper(), 'type': incident_type, 'severity': severity, 'route_id': route_id, 'stop_id': stop_id, 'lat': lat, 'lon': lon, 'delay_impact_minutes': delay_impact_minutes, 'description': description, 'status': 'active', 'reported_at': datetime.now()}
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_table(df, PROCESSED_DIR / 'incidents.parquet')
    return {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in row.items()}


def active_incidents(route_id: str | None = None) -> list[dict]:
    df = load_incidents()
    if df.empty:
        return []
    df = df[df['status'].isin(['active', 'monitoring'])]
    if route_id:
        df = df[df['route_id'].astype(str).eq(str(route_id))]
    if 'reported_at' in df.columns:
        df['reported_at'] = pd.to_datetime(df['reported_at']).astype(str)
        df = df.sort_values('reported_at', ascending=False)
    return df.to_dict(orient='records')


def resolve_incident(incident_id: str) -> dict:
    df = load_incidents()
    if df.empty or incident_id not in set(df['incident_id'].astype(str)):
        return {'status': 'not_found', 'incident_id': incident_id}
    df.loc[df['incident_id'].astype(str).eq(str(incident_id)), 'status'] = 'resolved'
    save_table(df, PROCESSED_DIR / 'incidents.parquet')
    return {'status': 'resolved', 'incident_id': incident_id}

# Backward-compatible helper.
def add_incident(location_stop_id: str, severity: str, delay_minutes: float, description: str):
    report_incident('driver_report', severity, 'UNKNOWN', location_stop_id, 0.0, 0.0, delay_minutes, description)
    return load_incidents()
