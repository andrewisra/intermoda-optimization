# AI Transit Synchronizer (AITS)

AITS adalah prototype **AI-Based Intermodal Transit Synchronization System** untuk Case 2: **Public Transit Optimization and Intermodal Connectivity**.

Sistem ini menempatkan **moda rel (MRT/LRT/KRL) sebagai fixed schedule anchor** yang tidak diinterupsi. AI dan optimizer digunakan untuk menyesuaikan moda non-rel seperti TransJakarta, Mikrotrans, feeder bus, atau school bus agar koneksi antarmoda lebih sinkron dan waiting time target tetap di bawah 8 menit.

## Fitur utama

1. **AI ETA Delay Prediction**  
   Model ML memprediksi keterlambatan/ETA moda non-rel berdasarkan rute, halte, jam, hari, kondisi traffic, hujan, insiden, dan kepadatan.

2. **AI Passenger Density Prediction**  
   Model ML memprediksi tingkat kepadatan halte/kendaraan: `LOW`, `MEDIUM`, `HIGH`, atau `OVERLOADED`.

3. **Personalized Walking Time**  
   Waktu jalan kaki antarmoda dikategorikan menjadi `VERY_SHORT`, `SHORT`, `MEDIUM`, `LONG`, dan `VERY_LONG`. Dengan izin pengguna, waktu ini dipersonalisasi berdasarkan profil kemampuan berjalan.

4. **Missed-Connection Risk Scoring**  
   Sistem menghitung risiko gagal mengejar moda berikutnya berdasarkan ETA, walking time, jadwal rel fixed, density, dan uncertainty.

5. **Rail-Fixed Intermodal Optimizer**  
   Jadwal MRT/LRT/KRL tidak diubah. Sistem hanya mengoptimalkan moda non-rel melalui rekomendasi:
   - `CONNECT`: koneksi aman.
   - `HOLD_NON_RAIL`: tahan bus/feeder 1-3 menit jika feasible.
   - `REDIRECT_NEXT_SERVICE`: arahkan penumpang ke layanan berikutnya.
   - `DISPATCH_EXTRA_FLEET`: siapkan armada berikutnya jika kepadatan tinggi.
   - `SAFE_SPEED_ADJUSTMENT`: rekomendasi kecepatan aman dalam batas legal.

6. **FastAPI Backend + Streamlit Dashboard**  
   Backend menyediakan API untuk prediksi ETA, prediksi kepadatan, optimasi transfer, laporan insiden, dan KPI simulator. Dashboard memperlihatkan alur end-to-end.

---

## Struktur folder

```text
ai_transit_synchronizer/
  backend/
    app/
      main.py
      routes/
      schemas.py
      services.py
  data/
    raw/
    processed/
  frontend/
    dashboard/
      app.py
  models/
  scripts/
    bootstrap_demo.py
    run_api.py
    train_models.py
  src/
    aits/
      config.py
      data/
      ml/
      optimizer/
      simulator/
  tests/
  README.md
  requirements.txt
```

---

## Quick start

### 1. Buat virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependency

```bash
pip install -r requirements.txt
```

### 3. Generate data demo dan train AI models

```bash
python scripts/bootstrap_demo.py
python scripts/train_models.py
```

### 4. Jalankan backend

```bash
uvicorn backend.app.main:app --reload
```

Buka docs:

```text
http://127.0.0.1:8000/docs
```

### 5. Jalankan dashboard

Terminal baru:

```bash
streamlit run frontend/dashboard/app.py
```

---

## API utama

### Health check

```text
GET /
```

### Predict ETA

```text
POST /api/predict/eta
```

Example body:

```json
{
  "route_id": "TJ_01",
  "stop_id": "TJ_DUKUH_ATAS",
  "hour": 7,
  "day_of_week": 1,
  "traffic_level": 4,
  "rainfall_level": 1,
  "incident_flag": 0,
  "passenger_density_score": 0.55,
  "scheduled_travel_minutes": 12
}
```

### Predict density

```text
POST /api/predict/density
```

Example body:

```json
{
  "stop_id": "TJ_DUKUH_ATAS",
  "route_id": "TJ_01",
  "hour": 7,
  "day_of_week": 1,
  "tap_in_count_15m": 95,
  "scheduled_headway_minutes": 8,
  "vehicle_capacity": 80,
  "event_flag": 0,
  "rainfall_level": 1
}
```

### Optimize transfer

```text
POST /api/optimize/transfer
```

Example body:

```json
{
  "user_id": "U_STANDARD",
  "from_stop_id": "TJ_DUKUH_ATAS",
  "to_station_id": "MRT_DUKUH_ATAS",
  "route_id": "TJ_01",
  "current_time": "2026-05-23T07:30:00",
  "scheduled_non_rail_arrival": "2026-05-23T07:38:00",
  "traffic_level": 3,
  "rainfall_level": 0,
  "incident_flag": 0,
  "tap_in_count_15m": 85,
  "vehicle_capacity": 80,
  "scheduled_headway_minutes": 8
}
```

---

## Cara kerja optimizer

Pseudocode:

```text
rail_departure_time = fixed
non_rail_arrival = AI_ETA_prediction
walking_time = transfer_category_default_time * user_multiplier
passenger_ready_time = non_rail_arrival + walking_time
waiting_time = rail_departure_time - passenger_ready_time

if 0 <= waiting_time <= 8:
    CONNECT
elif passenger_ready_time > rail_departure_time:
    choose next rail departure
    if current non-rail can be held safely:
        HOLD_NON_RAIL
    else:
        REDIRECT_NEXT_SERVICE
elif waiting_time > 8:
    try earlier/later feasible service or safe speed adjustment

if density is HIGH or OVERLOADED:
    add recommendation DISPATCH_EXTRA_FLEET
```

Catatan utama: **rail schedule is never modified**.

---

## AI model yang digunakan

Prototype memakai model yang kuat namun tetap realistis untuk lomba dan data terbatas:

1. **RandomForestRegressor** untuk ETA delay prediction.
   - Cocok untuk data tabular.
   - Robust terhadap data non-linear.
   - Cepat dilatih.
   - Mudah dijelaskan ke juri.

2. **RandomForestClassifier** untuk passenger density classification.
   - Cocok untuk klasifikasi `LOW`, `MEDIUM`, `HIGH`, `OVERLOADED`.
   - Bisa bekerja baik pada data tabular awal.
   - Tidak membutuhkan deep learning atau data masif.

Untuk produksi, model bisa ditingkatkan ke LightGBM/XGBoost atau temporal model jika data historis real-time sudah tersedia.

---

## Data yang digunakan dalam prototype

Prototype menghasilkan data demo/sintetis yang merepresentasikan:

- jadwal rail fixed;
- jadwal/arrival non-rel;
- transfer node dan walking time category;
- user walking profile;
- tap-in/tap-out sintetis;
- fitur traffic, rainfall, incident;
- kapasitas armada;
- data training ETA dan density.

Untuk deployment produksi, data harus diganti dengan data operator:

- GPS/AVL armada;
- AFC tap-in/tap-out anonymized;
- schedule actual vs planned;
- fleet registry;
- incident logs;
- CCTV/sensor/ATCS/Jakarta Smart City data.

---

## Run test

```bash
pytest
```

---

## Demo story untuk presentasi

1. Pilih user profile: standard, relaxed, assisted mobility.
2. Pilih transfer node, misalnya `TJ_DUKUH_ATAS -> MRT_DUKUH_ATAS`.
3. Sistem memprediksi ETA bus dengan model AI.
4. Sistem mempersonalisasi walking time.
5. Sistem mencari jadwal rail berikutnya tanpa mengubah jadwal rel.
6. Sistem menghitung waiting time dan missed-connection risk.
7. Sistem memberi rekomendasi operasional.
8. Dashboard menampilkan KPI: average waiting time, risk score, density level, dan decision.

---

## One-liner proposal

AITS treats MRT/LRT/KRL as fixed schedule anchors and uses AI-based ETA prediction, passenger density forecasting, personalized walking-time estimation, missed-connection risk scoring, and constraint-based optimization to synchronize flexible non-rail modes and reduce intermodal waiting time below 8 minutes.
