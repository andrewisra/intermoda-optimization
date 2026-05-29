# Mapping Proposal Claim to Prototype Code

| Proposal claim | Prototype module | Evidence in code |
|---|---|---|
| Accurate ETA and schedule optimization | `src/eta/baseline_eta.py`, `src/eta/train_eta_model.py` | Computes next arrivals and trains a RandomForest delay correction model. |
| Intermodal transfer optimization | `src/simulator/transfer_simulator.py`, `src/optimizer/connection_optimizer.py` | Combines first-mode ETA, walking time, next-mode departure, and the 8-minute waiting threshold. |
| Dwell time recommendation | `src/optimizer/dwell_time_optimizer.py` | Recommends whether a non-rail vehicle should hold within the allowed dwell extension. |
| Passenger density detection | `src/density/stop_density.py`, `src/density/load_factor.py` | Uses synthetic tap-in/tap-out records and load factor thresholds. |
| Safe speed adjustment | `src/optimizer/speed_adjustment.py` | Recommends speed increase/decrease within configured safety limits. |
| Driver/operator incident reporting | `src/incident/incident_report.py`, `backend/app/routes/incidents.py` | Stores operational disruptions and exposes an API endpoint. |
| App/website integration | `backend/app/main.py`, `frontend/dashboard/app.py` | Provides FastAPI endpoints and a Streamlit dashboard. |
| Prototype-ready data approach | `src/data_pipeline/generate_demo_data.py`, `src/data_pipeline/import_halte_excel.py` | Generates controlled demo data and can import the provided halte spreadsheet. |
