# Implementation Plan: Evolving Intermoda-Optimization to Production-Grade

## Problem & Background

The [prep.md](file:///d:/Coding/localrepositories/intermoda-optimization/prep.md) document is a comprehensive deep-research brief for **Case 2: Public Transit Optimization and Intermodal Connectivity** in the AI Open Innovation Challenge 2026. It identifies the full data landscape, operator statistics, API sources, privacy requirements, and architectural gaps needed to build a credible AI-Based Intermodal Transit Synchronization System for DKI Jakarta.

The current prototype is a **functional MVP** with 7 demo stops, 4 transfer nodes, ~80 schedule entries, 400 synthetic tap-in records, a RandomForest delay model, FastAPI backend, and Streamlit dashboard. However, there are significant gaps between what exists and what prep.md requires for a convincing competition prototype.

### Current State Summary

| Area | What Exists | Gap vs. prep.md |
|---|---|---|
| **Network** | 7 stops (3 TJ, 3 MRT, 1 KRL), 4 transfer nodes | prep.md names 6+ priority hubs (Dukuh Atas, Tanah Abang, Manggarai, Harmoni, Blok M, Lebak Bulus); real Transjakarta GTFS has ~4,500 stops |
| **Schedules** | 80 hardcoded trips (24 TJ, 36 MRT, 20 KRL) | No real GTFS integration; prep.md says GTFS Transjakarta is "prototype-ready today" |
| **Tap-in data** | 400 synthetic records, 4 stops only | prep.md requires realistic OD matrix, hourly density, transfer chains |
| **Fleet** | 4-row capacity table (generic) | prep.md specifies per-vehicle-type capacity with sensitivity analysis |
| **ML Model** | Single RandomForest, 6 features, ~0.98 MAE | prep.md expects traffic/ATCS, weather/flood, incident severity as features |
| **External data** | None | prep.md identifies PetaBencana flood API, BMKG weather, TUMI traffic as public & usable |
| **Dashboard** | Single-page Streamlit with basic map | prep.md expects KPI dashboard, density hotspots, disruption map, scenario simulator |
| **Tests** | 2 unit tests for connection_optimizer | Minimal coverage |
| **KPIs** | None defined | prep.md defines: ETA error, headway adherence, load factor, waiting time, transfer miss rate, fleet utilization |

---

## User Review Required

> [!IMPORTANT]
> **GTFS Download**: prep.md provides the Transjakarta GTFS URL (`gtfs.transjakarta.co.id/files/file_gtfs.zip`). Should we download and integrate it into the prototype pipeline automatically, or keep using synthetic-only data for now? Downloading real GTFS would make the demo dramatically more credible but adds external dependency.

> [!IMPORTANT]
> **Target Transfer Nodes**: prep.md suggests 6 priority hubs: Dukuh Atas, Tanah Abang, Manggarai, Harmoni, Blok M, and Lebak Bulus. Currently only Dukuh Atas area is modeled (with Blok M and Bundaran HI stops but only 2 transfer links from Dukuh Atas). Should we expand to all 6 hubs with curated walking times?

> [!WARNING]
> **Scope vs. Time**: The full prep.md vision is enormous. This plan prioritizes the highest-impact items that bridge the gap between "demo with 7 stops" and "credible competition prototype with real data shape." Production features like live GPS integration, CCTV occupancy, and operator MoU are explicitly deferred.

## Open Questions

1. **GTFS Integration Depth**: Download real GTFS and parse into the pipeline (adds ~4,500 stops, ~250 routes, thousands of trips), or expand synthetic data to ~30-50 representative stops across all 6 priority hubs?
2. **External API Integration**: Should we add live calls to PetaBencana flood API and BMKG weather during prototype, or mock their responses with realistic synthetic data?
3. **Dashboard Hosting**: Streamlit is good for demo but prep.md mentions JakLingko integration. Stay with Streamlit for competition, or add a lightweight React/HTML frontend?
4. **Competition Deadline**: How many days remain? This affects which phases to prioritize.

---

## Proposed Changes

### Phase 1 — Expanded Network & Transfer Graph

Expand from 7 stops / 4 transfer nodes to all 6 priority hubs identified in prep.md with realistic coordinates, walking times, and multi-modal connections.

---

#### [MODIFY] [generate_demo_data.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/data_pipeline/generate_demo_data.py)

- Expand `make_stops()` from 7 to ~25-30 stops covering all 6 priority hubs:
  - **Dukuh Atas**: TJ, MRT, KRL Sudirman (already exists, keep)
  - **Blok M**: TJ, MRT (exists, keep)
  - **Bundaran HI**: TJ, MRT (exists, keep)
  - **Tanah Abang**: TJ, KRL (new)
  - **Manggarai**: TJ, KRL (new)
  - **Harmoni**: TJ (new — major BRT hub)
  - **Lebak Bulus**: TJ, MRT (new — southern terminus)
  - **Cawang**: TJ, LRT (new)
  - **Velodrome**: LRT (new)
  - **Kampung Bandan**: TJ, KRL (new)
  - Add Mikrotrans feeder stops near 2-3 hubs
- Expand `make_transfer_nodes()` to ~15-20 links covering all hub-to-hub intermodal transfers
- Expand `make_schedules()` to generate trips for all new stops/routes with realistic headways:
  - Transjakarta: 5-8 min peak, 10-15 min off-peak
  - MRT: 5 min peak, 10 min off-peak
  - KRL: 6-10 min peak, 15-20 min off-peak
  - LRT: 10 min headway
- Expand `make_synthetic_tapin()` from 400 to ~2,000-3,000 records across all stops with realistic OD distribution
- Add `make_holidays_calendar()` for demand seasonality flags
- Expand `make_incidents()` to ~8-10 sample incidents across different hubs and severity levels

---

#### [NEW] [src/data_pipeline/download_gtfs.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/data_pipeline/download_gtfs.py)

- Script to download official Transjakarta GTFS ZIP from `gtfs.transjakarta.co.id/files/file_gtfs.zip`
- Extract to `data/raw/gtfs_transjakarta/`
- Validate that required files exist (`stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`)
- Integrate with existing `parse_gtfs.py` pipeline
- Add `--offline` flag to skip download if files already exist

---

#### [MODIFY] [parse_gtfs.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/data_pipeline/parse_gtfs.py)

- Parse additional GTFS files: `shapes.txt`, `calendar.txt`, `calendar_dates.txt`
- Normalize time fields (GTFS uses `HH:MM:SS` strings that can exceed 24:00:00)
- Build route-stop graph from parsed data
- Generate `transfer_nodes` automatically by finding stops within 500m of each other across different modes

---

### Phase 2 — Fleet Capacity & KPI Framework

Build the supply-side data model and KPI computation layer that prep.md identifies as critical for credible optimization.

---

#### [MODIFY] [generate_demo_data.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/data_pipeline/generate_demo_data.py)

- Expand `make_fleet_capacity()` to include per-vehicle-type breakdown matching prep.md Section 6.2:
  - Transjakarta: single_bus (80 pax), articulated_bus (120 pax), low_entry_bus (60 pax), microtrans (12 pax)
  - MRT: trainset_4car (800 pax), trainset_6car (1200 pax)
  - KRL: trainset_8car (1600 pax), trainset_12car (2000 pax)
  - LRT: trainset_2car (270 pax), trainset_4car (540 pax)
- Add `route_assignment`, `depot_id`, `active_status` fields
- Add `make_vehicle_positions()` with simulated GPS traces for ~20 vehicles across key corridors

---

#### [NEW] [src/kpi/metrics.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/kpi/metrics.py)

Define KPI computation functions matching prep.md Section 15 item 6:
- `eta_error(predicted, actual)` → MAE in minutes
- `headway_adherence(scheduled_headways, actual_headways)` → percentage within ±2 min
- `load_factor_distribution(tap_counts, capacities)` → histogram + mean/p95
- `passenger_waiting_time(transfer_results)` → mean/p50/p95 waiting minutes
- `transfer_miss_rate(transfer_results)` → percentage of `missed_connection` decisions
- `fleet_utilization(trips_completed, trips_planned)` → ratio

---

#### [NEW] [backend/app/routes/kpi.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/routes/kpi.py)

- `GET /kpi/summary` → all KPIs for a given time window
- `GET /kpi/eta-accuracy` → ETA error distribution
- `GET /kpi/transfer-performance` → waiting time & miss rate
- `GET /kpi/load-factors` → load factor by route/stop

---

### Phase 3 — External Data Integration (Weather, Flood, Traffic)

Integrate the public APIs identified in prep.md as "prototype-ready today."

---

#### [NEW] [src/external/petabencana.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/external/petabencana.py)

- Fetch flood gauge data from `https://data.petabencana.id/floodgauges?admin=ID-JK`
- Fetch flood affected areas from `https://data.petabencana.id/floods?admin=ID-JK&minimum_state=1`
- Parse GeoJSON responses into DataFrame with columns: `gauge_id`, `lat`, `lon`, `water_level`, `severity`, `timestamp`
- Cache responses for 15 minutes to avoid hammering the API
- Provide fallback synthetic flood data when offline/API unavailable

---

#### [NEW] [src/external/bmkg_weather.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/external/bmkg_weather.py)

- Fetch weather data from BMKG MEWS ArcGIS REST service
- Parse into: `station`, `temperature`, `rainfall_mm`, `wind_speed`, `is_heavy_rain`, `timestamp`
- Map rainfall intensity to delay factors using `delay_adjustment.py` logic
- Cache responses for 30 minutes
- Provide fallback synthetic weather when offline

---

#### [MODIFY] [delay_adjustment.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/eta/delay_adjustment.py)

- Add `delay_from_flood(water_level_cm)` using PetaBencana severity levels
- Add `combined_delay(incidents, weather, flood)` that aggregates all external disruption sources
- Wire external sources into `estimate_eta_with_incident()` in `baseline_eta.py`

---

#### [MODIFY] [baseline_eta.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/eta/baseline_eta.py)

- Update `estimate_eta_with_incident()` to call combined delay from weather + flood + incidents
- Add route-level delay aggregation (not just max incident delay)

---

### Phase 4 — ML Model Enhancement

Upgrade the ML pipeline from basic RandomForest to a more credible and explainable model.

---

#### [MODIFY] [train_eta_model.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/eta/train_eta_model.py)

- Add `GradientBoostingRegressor` as alternative model with hyperparameter tuning
- Expand feature set to include:
  - `flood_flag`: from PetaBencana integration
  - `weather_severity`: from BMKG integration
  - `route_length_km`: from GTFS shapes
  - `transfer_node_flag`: whether stop is a major hub
  - `demand_percentile`: hourly demand rank from tap-in data
- Add cross-validation with 5-fold CV
- Store feature importances alongside model for explainability
- Add model comparison table (RF vs GB) in training output
- Save training metadata (timestamp, features, metrics, dataset size) as JSON

---

#### [NEW] [src/eta/demand_forecast.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/eta/demand_forecast.py)

- Hourly demand prediction per stop using historical tap-in patterns
- Features: `hour`, `dayofweek`, `is_holiday`, `is_peak`, `weather_flag`, `stop_id` (encoded)
- Output: predicted tap-in count for next 1-4 hours
- Used by dashboard for proactive crowding alerts

---

#### [NEW] [src/optimizer/headway_optimizer.py](file:///d:/Coding/localrepositories/intermoda-optimization/src/optimizer/headway_optimizer.py)

- Given demand forecast + fleet capacity + current headway → recommend adjusted headway
- Constraint: minimum headway per mode (MRT/KRL cannot go below scheduled), maximum headway for service quality
- Output: `route_id`, `current_headway_minutes`, `recommended_headway_minutes`, `reason`, `demand_supply_ratio`
- This directly addresses prep.md's "schedule optimization" requirement

---

### Phase 5 — Backend API Expansion

Add missing endpoints and harden the API layer.

---

#### [NEW] [backend/app/routes/schedule.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/routes/schedule.py)

- `GET /schedule/headway?route_id=...&current_time=...` → current and recommended headway
- `GET /schedule/trips?route_id=...&start_time=...&end_time=...` → trip list with stop sequence
- `POST /schedule/optimize` → run headway optimizer for a given time window and return recommendations

---

#### [NEW] [backend/app/routes/forecast.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/routes/forecast.py)

- `GET /forecast/demand?stop_id=...&hours_ahead=4` → predicted demand per hour
- `GET /forecast/crowding-alerts?current_time=...` → stops expected to exceed capacity in next 2 hours

---

#### [NEW] [backend/app/routes/external.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/routes/external.py)

- `GET /external/flood` → current flood gauges and affected areas from PetaBencana
- `GET /external/weather` → current weather conditions from BMKG
- `GET /external/disruptions` → combined view of all active disruptions (incidents + flood + weather)

---

#### [MODIFY] [main.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/main.py)

- Register new routers: `schedule`, `forecast`, `external`, `kpi`
- Add startup event to ensure demo data exists and model is trained
- Add structured error handling middleware
- Add request logging middleware

---

#### [MODIFY] [schemas.py](file:///d:/Coding/localrepositories/intermoda-optimization/backend/app/models/schemas.py)

- Add response models for new endpoints: `KPISummary`, `DemandForecast`, `HeadwayRecommendation`, `FloodGauge`, `WeatherCondition`, `DisruptionSummary`
- Add `HeadwayOptimizeRequest` with `route_id`, `time_window_start`, `time_window_end`

---

### Phase 6 — Dashboard Overhaul

Transform the single-page Streamlit dashboard into a multi-page application with proper KPI visualization.

---

#### [MODIFY] [frontend/dashboard/app.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/app.py)

- Convert to multi-page Streamlit app using `st.navigation` / page directory structure
- Main page becomes overview with KPI summary cards

---

#### [NEW] [frontend/dashboard/pages/1_kpi_overview.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/pages/1_kpi_overview.py)

- KPI metric cards: avg waiting time, transfer miss rate, ETA accuracy, fleet utilization
- Trend charts using Plotly for ridership over time (from tap-in data)
- Mode distribution pie chart
- Peak vs off-peak comparison

---

#### [NEW] [frontend/dashboard/pages/2_transfer_simulator.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/pages/2_transfer_simulator.py)

- Move and enhance the existing transfer simulation UI
- Add all 6 priority hubs as selectable origins/destinations
- Add scenario comparison: "what if delay is 5 min" vs "what if delay is 10 min"
- Show decision tree visualization for the optimizer logic

---

#### [NEW] [frontend/dashboard/pages/3_density_map.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/pages/3_density_map.py)

- Full-screen PyDeck map with density heatmap layer
- Color-coded stops by density level (low/medium/high/very_high)
- Animated time slider to show density changes throughout the day
- Overlay flood zones from PetaBencana data
- Overlay active incidents

---

#### [NEW] [frontend/dashboard/pages/4_demand_forecast.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/pages/4_demand_forecast.py)

- Demand forecast charts per stop for next 4 hours
- Crowding alert table: which stops will exceed thresholds
- Headway recommendation table from optimizer

---

#### [NEW] [frontend/dashboard/pages/5_incident_manager.py](file:///d:/Coding/localrepositories/intermoda-optimization/frontend/dashboard/pages/5_incident_manager.py)

- Move and enhance incident reporting form
- Incident timeline view (chronological)
- Active incidents table with resolve actions
- Impact analysis: which routes/stops affected, estimated delay

---

### Phase 7 — Testing, Documentation & Polish

---

#### [MODIFY] [tests/test_optimizer.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_optimizer.py)

- Add tests for edge cases: exactly at threshold, negative ETA, zero capacity

---

#### [NEW] [tests/test_eta.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_eta.py)

- Test `next_arrivals` with various stop/time combinations
- Test `estimate_eta_with_incident` with active incidents
- Test model training pipeline end-to-end

---

#### [NEW] [tests/test_density.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_density.py)

- Test density calculation with known tap-in counts
- Test load factor thresholds
- Test `density_by_stop` aggregation

---

#### [NEW] [tests/test_kpi.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_kpi.py)

- Test each KPI computation function with known inputs/outputs

---

#### [NEW] [tests/test_external.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_external.py)

- Test PetaBencana and BMKG parsers with mock responses
- Test fallback to synthetic data when API unavailable

---

#### [NEW] [tests/test_api.py](file:///d:/Coding/localrepositories/intermoda-optimization/tests/test_api.py)

- Integration tests using FastAPI TestClient for all endpoints
- Test error responses for invalid inputs
- Test response schemas match Pydantic models

---

#### [MODIFY] [README.md](file:///d:/Coding/localrepositories/intermoda-optimization/README.md)

- Update project structure section
- Add architecture diagram (Mermaid)
- Update endpoint list with new routes
- Add KPI definitions section
- Update data sources section referencing prep.md findings

---

#### [MODIFY] [PROPOSAL_CODE_MAPPING.md](file:///d:/Coding/localrepositories/intermoda-optimization/docs/PROPOSAL_CODE_MAPPING.md)

- Add mappings for new modules: KPI, demand forecast, headway optimizer, external APIs, expanded dashboard

---

#### [NEW] [docs/DATA_SOURCES.md](file:///d:/Coding/localrepositories/intermoda-optimization/docs/DATA_SOURCES.md)

- Curated version of prep.md Section 13 (Source Inventory) with only the sources actually used or integrated
- Status column: `integrated`, `ready_to_integrate`, `requires_MoU`

---

#### [NEW] [docs/KPI_DEFINITIONS.md](file:///d:/Coding/localrepositories/intermoda-optimization/docs/KPI_DEFINITIONS.md)

- Formal definition of each KPI with formula, threshold, and data source
- Mapping to proposal claims

---

## Verification Plan

### Automated Tests

```bash
make test
```

All tests in `tests/` must pass, covering:
- Connection optimizer (existing + new edge cases)
- ETA baseline and incident-aware ETA
- Density calculation and load factor
- KPI computation
- External API parsers with mock data
- FastAPI endpoint integration tests

### Manual Verification

1. **`make data`** → verify expanded dataset:
   - `stops.parquet` should have 25-30 rows
   - `transfer_nodes.parquet` should have 15-20 rows
   - `schedules.parquet` should have 300+ trips
   - `synthetic_tapin.parquet` should have 2,000+ records
   - `fleet_capacity.parquet` should have 8-10 vehicle types

2. **`make api`** → verify all endpoints return valid JSON:
   - `GET /` → health check
   - `GET /eta/next?stop_id=TJ_DUKUH_ATAS&current_time=2026-05-23T07:20:00`
   - `POST /optimizer/transfer` with new hub combinations
   - `GET /kpi/summary?start_time=2026-05-23T07:00:00&end_time=2026-05-23T09:00:00`
   - `GET /forecast/demand?stop_id=TJ_DUKUH_ATAS&hours_ahead=4`
   - `GET /external/disruptions`
   - `GET /schedule/headway?route_id=TJ_1&current_time=2026-05-23T07:20:00`

3. **`make dashboard`** → verify multi-page dashboard:
   - KPI Overview page loads with metric cards and charts
   - Transfer Simulator works with all 6 priority hubs
   - Density Map shows color-coded stops with heatmap
   - Demand Forecast shows prediction charts
   - Incident Manager allows reporting and viewing incidents

4. **`docker compose up --build`** → verify containerized deployment works end-to-end
