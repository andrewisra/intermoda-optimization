from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import uuid
import pandas as pd

from src.aits.config import RAW_DIR
from src.aits.data import repository as repo
from src.aits.ml.predict import registry
from src.aits.optimizer.intermodal import optimize_transfer
from src.aits.simulator.simulate import run_demo_scenarios


def predict_eta_service(payload: dict) -> dict:
    return asdict(registry.predict_eta_delay(payload))


def predict_density_service(payload: dict) -> dict:
    return asdict(registry.predict_density(payload))


def optimize_transfer_service(payload: dict) -> dict:
    result = optimize_transfer(**payload)
    return asdict(result)


def list_reference_data() -> dict:
    return {
        "stops": repo.stops().to_dict(orient="records"),
        "routes": repo.routes().to_dict(orient="records"),
        "transfer_nodes": repo.transfer_nodes().to_dict(orient="records"),
        "user_profiles": repo.user_profiles().to_dict(orient="records"),
    }


def create_incident(payload: dict) -> dict:
    path = RAW_DIR / "incidents.csv"
    df = repo.incidents()
    row = {
        "incident_id": f"INC_{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.now().isoformat(),
        "location_stop_id": payload["location_stop_id"],
        "incident_type": payload["incident_type"].upper(),
        "severity": payload["severity"],
        "description": payload["description"],
        "is_active": True,
    }
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    new_df.to_csv(path, index=False)
    repo.clear_cache()
    return row


def simulator_service() -> dict:
    df = run_demo_scenarios()
    return {"scenarios": df.to_dict(orient="records")}
