from __future__ import annotations

from datetime import datetime, timedelta
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Allow running Streamlit from project root.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services import list_reference_data, optimize_transfer_service, predict_eta_service, predict_density_service, simulator_service

st.set_page_config(page_title="AI Transit Synchronizer", layout="wide")
st.title("AI Transit Synchronizer")
st.caption("Rail-fixed AI intermodal optimization for Case 2: Public Transit Optimization and Intermodal Connectivity")

ref = list_reference_data()
transfers = pd.DataFrame(ref["transfer_nodes"])
users = pd.DataFrame(ref["user_profiles"])
stops = pd.DataFrame(ref["stops"])

with st.sidebar:
    st.header("Scenario Input")
    transfer_label = st.selectbox(
        "Transfer node",
        [f"{r.from_stop_id} -> {r.to_station_id}" for r in transfers.itertuples()],
    )
    selected_transfer = transfers.iloc[[f"{r.from_stop_id} -> {r.to_station_id}" for r in transfers.itertuples()].index(transfer_label)]
    user_id = st.selectbox("User mobility profile", users["user_id"].tolist(), index=1)
    route_id = st.selectbox("Non-rail route", ["TJ_01", "TJ_02", "MKT_01"])
    current_time = st.time_input("Current time", value=datetime(2026, 5, 23, 7, 30).time())
    base_dt = datetime(2026, 5, 23, current_time.hour, current_time.minute)
    scheduled_arrival_min = st.slider("Scheduled non-rail arrival in minutes", 3, 25, 8)
    traffic_level = st.slider("Traffic level", 0, 5, 3)
    rainfall_level = st.slider("Rainfall level", 0, 5, 0)
    incident_flag = st.selectbox("Incident flag", [0, 1])
    tap_in_count_15m = st.slider("Tap-in count last 15 min", 0, 180, 80)
    vehicle_capacity = st.number_input("Vehicle capacity", min_value=1, value=80)
    headway = st.number_input("Scheduled headway minutes", min_value=1, value=8)

payload = {
    "user_id": user_id,
    "from_stop_id": selected_transfer["from_stop_id"],
    "to_station_id": selected_transfer["to_station_id"],
    "route_id": route_id,
    "current_time": base_dt,
    "scheduled_non_rail_arrival": base_dt + timedelta(minutes=scheduled_arrival_min),
    "traffic_level": traffic_level,
    "rainfall_level": rainfall_level,
    "incident_flag": int(incident_flag),
    "tap_in_count_15m": int(tap_in_count_15m),
    "vehicle_capacity": int(vehicle_capacity),
    "scheduled_headway_minutes": int(headway),
    "current_speed_kmh": 24.0,
}

result = optimize_transfer_service(payload)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Decision", result["decision"])
col2.metric("Waiting Time", f"{result['waiting_time_minutes']} min" if result["waiting_time_minutes"] is not None else "N/A")
col3.metric("Risk Score", result["risk_score"])
col4.metric("Density", result["density_level"])

st.subheader("Recommendation")
st.success(result["primary_recommendation"])
st.write(result["explanation"])

if result["additional_actions"]:
    st.subheader("Additional Operator Actions")
    st.json(result["additional_actions"])

st.subheader("Reference Map")
map_df = stops.dropna(subset=["lat", "lon"]).rename(columns={"lat": "latitude", "lon": "longitude"})
st.map(map_df[["latitude", "longitude"]])

st.subheader("AI Prediction Layer")
eta_features = {
    "route_id": route_id,
    "from_stop_id": selected_transfer["from_stop_id"],
    "to_stop_id": selected_transfer["to_station_id"],
    "route_mode": "TRANSJAKARTA",
    "scheduled_travel_seconds": scheduled_arrival_min * 60,
    "headway_minutes": float(headway),
    "hour": base_dt.hour,
    "day_of_week": base_dt.weekday(),
    "rainfall_level": rainfall_level,
    "flood_flag": 0,
    "temperature_c": 28,
    "historical_incident_rate": 0.05,
}
density_features = {
    "from_stop_id": selected_transfer["from_stop_id"],
    "route_id": route_id,
    "headway_minutes": float(headway),
    "vehicle_capacity": int(vehicle_capacity),
    "hour": base_dt.hour,
    "day_of_week": base_dt.weekday(),
    "rainfall_level": rainfall_level,
    "flood_flag": 0,
    "event_flag": 0,
}
colA, colB = st.columns(2)
with colA:
    st.markdown("**ETA model output**")
    st.json(predict_eta_service(eta_features))
with colB:
    st.markdown("**Density model output**")
    st.json(predict_density_service(density_features))

st.subheader("Scenario Simulator")
sim = pd.DataFrame(simulator_service()["scenarios"])
st.dataframe(sim, use_container_width=True)
fig = px.bar(sim, x="scenario", y="risk_score", color="decision", title="Missed-Connection Risk by Scenario")
st.plotly_chart(fig, use_container_width=True)
