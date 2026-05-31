# Transportation Synchronization

Transportation Synchronization adalah sistem prototype untuk **Public Transit Optimization and Intermodal Connectivity**. Sistem ini dirancang untuk membantu sinkronisasi perpindahan antarmoda di DKI Jakarta dengan prinsip utama:

> **Moda rel menjadi fixed schedule anchor, sedangkan moda non-rel dioptimalkan secara adaptif menggunakan AI.**

Artinya, sistem **tidak mengubah atau menahan jadwal MRT, LRT, dan KRL**. Sistem justru memprediksi kondisi perjalanan dan mengoptimalkan moda yang lebih fleksibel seperti TransJakarta, Mikrotrans, feeder bus, atau school bus agar waktu tunggu penumpang saat transit tetap rendah.

Target utama sistem adalah membantu menjaga **waiting time antarmoda di bawah 8 menit**, dengan mempertimbangkan ETA kendaraan, walking time, kepadatan penumpang, gangguan perjalanan, dan jadwal moda rel yang tetap.

---

## 1. Tujuan Sistem

TRANSYNC dibuat untuk menjawab masalah utama pada Case 2: ketidakpastian waktu kedatangan, belum optimalnya jadwal antarmoda, dan belum sinkronnya data antaroperator transportasi.

Sistem ini bertujuan untuk:

1. Memprediksi ETA moda non-rel secara adaptif.
2. Memprediksi tingkat kepadatan penumpang di halte/stasiun.
3. Menghitung walking time antarmoda secara kategori dan personal.
4. Mengukur risiko gagal koneksi atau missed connection.
5. Memberikan rekomendasi operasional berbasis constraint.
6. Menyediakan dashboard simulasi untuk pengguna/operator.
7. Menunjukkan bagaimana AI dapat membantu sinkronisasi antarmoda secara real-time.

---

## 2. Konsep Utama

### 2.1 Rail Fixed, Non-Rail Adaptive

Sistem membedakan moda transportasi menjadi dua kelompok:

| Kategori | Contoh | Perlakuan Sistem |
|---|---|---|
| Rail-based transport | MRT, LRT, KRL | Jadwal dianggap fixed dan tidak diinterupsi |
| Non-rail transport | TransJakarta, Mikrotrans, feeder, school bus | Dapat dioptimalkan melalui dwell time, dispatch, redirect, atau speed adjustment aman |

Strategi ini digunakan karena moda rel memiliki jadwal dan sistem operasi yang lebih ketat, sehingga tidak realistis jika sistem memaksa MRT/KRL/LRT menunggu penumpang. Sebaliknya, moda non-rel lebih fleksibel untuk disinkronkan dengan jadwal rel.

---

## 3. Arsitektur Sistem

Alur besar sistem:

```text
Input Data
  ├── GTFS TransJakarta
  ├── Jadwal rel fixed
  ├── Jadwal/posisi moda non-rel
  ├── Data tap-in/tap-out sintetis
  ├── Traffic level
  ├── Rainfall level
  ├── Incident flag
  ├── Transfer node dan walking time
  └── User mobility profile

        ↓

AI Prediction Layer
  ├── ETA Delay Prediction Model
  └── Passenger Density Prediction Model

        ↓

Decision & Optimization Layer
  ├── Personalized Walking Time Estimation
  ├── Missed-Connection Risk Scoring
  ├── Rail-Fixed Intermodal Optimizer
  └── Safe Speed Adjustment

        ↓

Output
  ├── API response
  ├── Dashboard simulation
  ├── Transfer recommendation
  ├── Operator action recommendation
  └── Scenario simulator
```

---

## 4. Fitur Utama

### 4.1 AI ETA Delay Prediction

Model AI pertama digunakan untuk memprediksi keterlambatan atau delay moda non-rel.

Input utama:

- `route_id`
- `stop_id`
- `hour`
- `day_of_week`
- `traffic_level`
- `rainfall_level`
- `incident_flag`
- `passenger_density_score`
- `scheduled_travel_minutes`

Output:

- `predicted_delay_minutes`
- `predicted_eta_minutes`
- `confidence_score`

Model yang digunakan:

```text
RandomForestRegressor
```

Alasan pemilihan:

- Cocok untuk data tabular transportasi.
- Tidak membutuhkan data sebesar deep learning.
- Cepat dilatih dan mudah dijelaskan.
- Cukup kuat untuk prototype AI innovation.
- Bisa diganti ke XGBoost/LightGBM pada tahap produksi.

---

### 4.2 AI Passenger Density Prediction

Model AI kedua digunakan untuk memprediksi tingkat kepadatan penumpang.

Input utama:

- `stop_id`
- `route_id`
- `hour`
- `day_of_week`
- `tap_in_count_15m`
- `scheduled_headway_minutes`
- `vehicle_capacity`
- `event_flag`
- `rainfall_level`

Output:

- `density_level`
- `density_score`
- `load_factor_estimation`

Kategori density:

| Level | Makna |
|---|---|
| LOW | Kepadatan rendah |
| MEDIUM | Kepadatan sedang |
| HIGH | Kepadatan tinggi |
| OVERLOADED | Melebihi kapasitas nyaman |

Model yang digunakan:

```text
RandomForestClassifier
```

---

### 4.3 Personalized Walking Time

Walking time tidak dianggap sama untuk semua orang. Sistem mendukung estimasi waktu jalan kaki berdasarkan kategori transfer dan profil mobilitas pengguna.

Kategori awal transfer:

| Kategori | Rentang | Default |
|---|---:|---:|
| VERY_SHORT | 1-5 menit | 4 menit |
| SHORT | 6-10 menit | 8 menit |
| MEDIUM | 11-15 menit | 13 menit |
| LONG | 16-20 menit | 18 menit |
| VERY_LONG | >20 menit | 23 menit |

Profil mobilitas pengguna:

| Profil | Multiplier | Makna |
|---|---:|---|
| FAST | 0.85 | Pengguna berjalan cepat |
| STANDARD | 1.00 | Pengguna berjalan normal |
| RELAXED | 1.25 | Pengguna membutuhkan waktu lebih santai |
| ASSISTED | 1.50 | Pengguna membutuhkan waktu transfer lebih lama |

Rumus:

```text
personalized_walking_time = default_walking_time × walking_multiplier
```

Jika pengguna tidak memberi izin personalisasi, sistem menggunakan profil standar.

---

### 4.4 Missed-Connection Risk Scoring

Sistem menghitung risiko penumpang gagal mengejar moda berikutnya.

Faktor yang diperhitungkan:

- ETA moda non-rel.
- Jadwal moda rel fixed.
- Personalized walking time.
- Kepadatan penumpang.
- Kondisi traffic.
- Hujan atau banjir.
- Incident flag.
- Buffer waktu transfer.

Output:

| Risk Score | Risk Level |
|---:|---|
| 0-30 | LOW |
| 31-60 | MEDIUM |
| 61-100 | HIGH |

Risk score ini menjadi dasar rekomendasi sistem.

---

### 4.5 Rail-Fixed Intermodal Optimizer

Optimizer adalah inti decision engine.

Constraint utama:

1. Jadwal MRT/LRT/KRL tidak boleh diubah.
2. Target waiting time ideal: kurang dari atau sama dengan 8 menit.
3. Hold moda non-rel maksimal 2-3 menit.
4. Speed adjustment harus dalam batas aman dan legal.
5. Kapasitas kendaraan tidak boleh overload.
6. Rekomendasi tidak boleh terlalu merugikan penumpang lain.

Decision output:

| Decision | Makna |
|---|---|
| CONNECT | Penumpang bisa lanjut ke moda berikutnya |
| HOLD_NON_RAIL | Moda non-rel disarankan menunggu sebentar |
| REDIRECT_TO_NEXT_SERVICE | Penumpang diarahkan ke layanan berikutnya |
| PREPARE_NEXT_FLEET | Operator perlu menyiapkan armada berikutnya |
| ADJUST_SPEED | Feeder disarankan menyesuaikan kecepatan aman |

Decision hierarchy:

```text
1. Coba hold moda non-rel jika gap kecil dan aman.
2. Jika hold tidak feasible, arahkan penumpang ke layanan berikutnya.
3. Jika kepadatan tinggi, siapkan armada berikutnya.
4. Jika perlu sinkronisasi tambahan, rekomendasikan speed adjustment aman.
```

Catatan penting: sistem tidak pernah menahan atau mengubah keberangkatan moda rel.

---

### 4.6 Safe Speed Adjustment

Speed adjustment bukan instruksi untuk "ngebut". Sistem hanya memberi rekomendasi dalam rentang aman.

Kemungkinan rekomendasi:

- Maintain normal speed.
- Slightly reduce speed to synchronize with next connection.
- Slightly increase speed only if still within safe and legal limits.

Tujuannya adalah sinkronisasi perjalanan, bukan mengejar jadwal secara berbahaya.

---

### 4.7 Incident Reporting

Sistem menyediakan mekanisme input insiden seperti:

- Kemacetan parah.
- Banjir.
- Kecelakaan.
- Gangguan operasional.
- Road closure.
- Laporan pengemudi.

Incident akan mempengaruhi:

- ETA prediction.
- Risk score.
- Transfer recommendation.
- Operator action.

---

## 5. Struktur Folder

```text
intermoda_aits_clean_refactor/
  backend/
    app/
      main.py
      routes/
        predict.py
        optimize.py
        data.py
        incidents.py
      services/
        aits_service.py
      models/
        schemas.py

  frontend/
    dashboard/
      app.py

  src/
    aits/
      data/
        demo_data.py
        gtfs_downloader.py
        gtfs_parser.py
        repositories.py
      ml/
        train.py
        predict.py
        features.py
      optimizer/
        intermodal.py
        walking_time.py
        risk.py
        speed.py
      simulator/
        scenarios.py
      incident/
        report.py
      config.py

  data/
    raw/
      gtfs_transjakarta.zip
      gtfs_transjakarta/
      stops.csv
      routes.csv
      transfer_nodes.csv
      user_profiles.csv
      rail_schedule.csv
      non_rail_schedule.csv
      incidents.csv
      training_eta.csv
      training_density.csv
    processed/

  models/
    eta_delay_model.joblib
    density_model.joblib
    metrics.json

  scripts/
    bootstrap_demo.py
    train_models.py

  tests/
  docs/
  README.md
  requirements.txt
```

---

## 6. Data yang Digunakan

### 6.1 Data Demo/Sintetis

Untuk prototype, sistem menggunakan data demo dan sintetis agar dapat dijalankan tanpa akses operator.

Data yang dibuat oleh `bootstrap_demo.py`:

- `stops.csv`
- `routes.csv`
- `transfer_nodes.csv`
- `user_profiles.csv`
- `rail_schedule.csv`
- `non_rail_schedule.csv`
- `incidents.csv`
- `training_eta.csv`
- `training_density.csv`

### 6.2 GTFS TransJakarta

Sistem mendukung GTFS TransJakarta untuk:

- Stop data.
- Route data.
- Trip data.
- Stop times.
- Shapes.
- Transfer node generation.

File GTFS dapat disimpan di:

```text
data/raw/gtfs_transjakarta.zip
```

atau diekstrak ke:

```text
data/raw/gtfs_transjakarta/
```

### 6.3 Data Produksi yang Dibutuhkan

Untuk implementasi production-grade, data yang ideal meliputi:

- Fleet GPS/AVL.
- Passenger tap-in/tap-out.
- Real-time traffic.
- Weather and flood data.
- Incident logs.
- Fleet registry and capacity.
- Actual trip logs.
- Service alerts.
- Station/halte crowding.

---

## 7. Instalasi di Windows

### 7.1 Prasyarat

Disarankan menggunakan:

```text
Python 3.11 atau 3.12
```

Python 3.13 bisa berjalan, tetapi beberapa package data science kadang lebih stabil di Python 3.11/3.12.

Cek versi Python:

```powershell
python --version
```

---

### 7.2 Buat Virtual Environment

Masuk ke folder project:

```powershell
cd D:\Kodingan\lomba_transport_ai\intermoda-optimization
```

Buat virtual environment:

```powershell
python -m venv .venv
```

Aktifkan virtual environment:

```powershell
.venv\Scripts\activate
```

Jika PowerShell menolak karena execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Lalu aktifkan ulang:

```powershell
.venv\Scripts\activate
```

---

### 7.3 Install Dependency

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Jika install terasa lama di package seperti `plotly`, `streamlit`, `pyarrow`, atau `scikit-learn`, tunggu beberapa menit. Di Windows hal tersebut normal.

---

## 8. Menjalankan Sistem

### 8.1 Generate Demo Data

Untuk generate data demo tanpa GTFS:

```powershell
python scripts\bootstrap_demo.py
```

Untuk generate data demo sekaligus memproses GTFS:

```powershell
python scripts\bootstrap_demo.py --with-gtfs --force-download --auto-transfers
```

Jika sudah punya `data/raw/gtfs_transjakarta.zip` dan ingin offline:

```powershell
python scripts\bootstrap_demo.py --with-gtfs --offline --auto-transfers
```

---

### 8.2 Train Model AI

```powershell
python scripts\train_models.py
```

Jika berhasil, akan muncul output seperti:

```json
{
  "eta": {
    "mae_minutes": 1.105,
    "rows": 4000
  },
  "density": {
    "accuracy": 0.998,
    "rows": 4000
  }
}
```

Catatan: metrik tersebut berasal dari data sintetis/demo, bukan data real-world operator.

---

### 8.3 Jalankan Backend

```powershell
uvicorn backend.app.main:app --reload
```

Buka API docs:

```text
http://127.0.0.1:8000/docs
```

---

### 8.4 Jalankan Dashboard

Buka terminal kedua:

```powershell
cd D:\Kodingan\lomba_transport_ai\intermoda-optimization
.venv\Scripts\activate
streamlit run frontend\dashboard\app.py
```

Dashboard akan tersedia di:

```text
http://localhost:8501
```

Jika Streamlit meminta email saat pertama kali dijalankan, kosongkan saja lalu tekan Enter.

---

## 9. Cara Menggunakan Dashboard

Dashboard digunakan sebagai simulator untuk membuktikan bagaimana TRANSYNC bekerja.

### 9.1 Input Skenario

Beberapa input utama:

| Input | Fungsi |
|---|---|
| Transfer node | Titik perpindahan, misalnya TransJakarta ke MRT |
| User mobility profile | Profil walking time pengguna |
| Non-rail route | Rute bus/feeder yang dioptimalkan |
| Current time | Waktu simulasi |
| Scheduled non-rail arrival | Perkiraan kedatangan bus/feeder sebelum koreksi AI |
| Traffic level | Kondisi lalu lintas |
| Rainfall level | Kondisi hujan/banjir |
| Incident flag | Ada/tidaknya insiden |
| Tap-in count last 15 min | Indikasi demand dan kepadatan |
| Vehicle capacity | Kapasitas kendaraan |
| Scheduled headway | Jarak antar kendaraan |

### 9.2 Output Dashboard

Output utama:

| Output | Makna |
|---|---|
| Decision | Rekomendasi sistem |
| Waiting Time | Estimasi waktu tunggu |
| Risk Score | Risiko gagal koneksi |
| Density Level | Prediksi kepadatan |
| ETA Prediction | Prediksi waktu kedatangan |
| Operator Action | Rekomendasi untuk operator |

---

## 10. Skenario Pengujian Manual

### 10.1 Kondisi Normal

Gunakan:

```text
Traffic level: 2
Rainfall level: 0
Incident flag: 0
Tap-in count: 40
Vehicle capacity: 80
```

Ekspektasi:

```text
Decision: CONNECT
Risk: LOW/MEDIUM
Density: LOW/MEDIUM
```

---

### 10.2 Macet dan Insiden

Gunakan:

```text
Traffic level: 5
Rainfall level: 3
Incident flag: 1
```

Ekspektasi:

```text
Risk score naik
Decision dapat berubah menjadi REDIRECT_TO_NEXT_SERVICE atau ADJUST_SPEED
```

---

### 10.3 Kepadatan Tinggi

Gunakan:

```text
Tap-in count last 15 min: 160
Vehicle capacity: 60
```

Ekspektasi:

```text
Density: HIGH atau OVERLOADED
Operator action: PREPARE_NEXT_FLEET
```

---

### 10.4 Walking Time Personal

Coba user berbeda:

```text
U001 = FAST
U002 = STANDARD
U003 = RELAXED
U004 = ASSISTED
```

Ekspektasi:

```text
Personalized walking time berubah
Risk score ikut berubah
Decision bisa berubah untuk user dengan walking time lebih lama
```

---

### 10.5 Rail Tidak Diinterupsi

Buat kondisi feeder terlambat:

```text
Scheduled non-rail arrival: 20-25 menit
Traffic level: 5
Incident flag: 1
```

Ekspektasi:

```text
Sistem tidak menahan MRT/KRL/LRT
Sistem memilih koneksi berikutnya atau mengoptimalkan non-rail mode
```

---

## 11. API Endpoint

### 11.1 Health Check

```http
GET /
```

---

### 11.2 ETA Prediction

```http
POST /api/predict/eta
```

Contoh request:

```json
{
  "route_id": "TJ_01",
  "stop_id": "TJ_DUKUH_ATAS",
  "hour": 7,
  "day_of_week": 0,
  "traffic_level": 4,
  "rainfall_level": 2,
  "incident_flag": 1,
  "passenger_density_score": 0.8,
  "scheduled_travel_minutes": 12
}
```

---

### 11.3 Density Prediction

```http
POST /api/predict/density
```

Contoh request:

```json
{
  "stop_id": "TJ_DUKUH_ATAS",
  "route_id": "TJ_01",
  "hour": 7,
  "day_of_week": 0,
  "tap_in_count_15m": 120,
  "scheduled_headway_minutes": 8,
  "vehicle_capacity": 80,
  "event_flag": 0,
  "rainfall_level": 1
}
```

---

### 11.4 Transfer Optimization

```http
POST /api/optimize/transfer
```

Contoh request:

```json
{
  "user_id": "U002",
  "from_stop_id": "TJ_DUKUH_ATAS",
  "to_station_id": "MRT_DUKUH_ATAS",
  "route_id": "TJ_01",
  "current_time": "2026-05-23T07:30:00",
  "scheduled_non_rail_arrival": "2026-05-23T07:38:00",
  "traffic_level": 3,
  "rainfall_level": 0,
  "incident_flag": 0,
  "tap_in_count_15m": 80,
  "vehicle_capacity": 80,
  "scheduled_headway_minutes": 8,
  "current_speed_kmh": 24
}
```

---

### 11.5 Reference Data

```http
GET /api/data/reference
```

---

### 11.6 Simulator Data

```http
GET /api/data/simulator
```

---

### 11.7 Incident Report

```http
POST /api/incidents
```

---

## 12. Testing

Jalankan:

```powershell
pytest
```

Ekspektasi:

```text
semua test passed
```

---

## 13. File Generated dan Git Ignore

File yang merupakan hasil generate/training dan boleh tidak di-commit:

```text
models/*.joblib
models/metrics.json
data/raw/training_eta.csv
data/raw/training_density.csv
data/processed/*
```

File demo kecil yang boleh tetap di-commit agar project mudah dijalankan:

```text
data/raw/stops.csv
data/raw/routes.csv
data/raw/transfer_nodes.csv
data/raw/user_profiles.csv
data/raw/rail_schedule.csv
data/raw/non_rail_schedule.csv
```

Contoh `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env

models/*.joblib
models/metrics.json

data/raw/training_eta.csv
data/raw/training_density.csv

data/processed/*
!data/processed/.gitkeep

.pytest_cache/
.streamlit/
```

---

## 14. Strategi Pengembangan Lanjutan

Untuk tahap berikutnya, sistem dapat dikembangkan dengan:

1. Integrasi GPS/AVL real-time dari operator.
2. Integrasi tap-in/tap-out anonymized.
3. Integrasi traffic speed, ATCS, cuaca, dan banjir.
4. Replacement model ke XGBoost atau LightGBM.
5. Penambahan real-time streaming pipeline.
6. Dashboard operator yang lebih detail.
7. User-facing app integration ke JakLingko.
8. Evaluasi fairness dan accessibility untuk pengguna disabilitas.
9. Deployment menggunakan Docker dan cloud service.
10. Model monitoring untuk drift dan performa ETA.

---

## 15. Catatan AI dan Data

Metrik pada prototype berasal dari data sintetis:

- ETA MAE sekitar 1.1 menit.
- Density accuracy sekitar 99.8%.

Metrik ini hanya menunjukkan bahwa pipeline AI berjalan dengan baik. Untuk klaim performa real-world, model harus dilatih ulang menggunakan data operator seperti GPS armada, tapping penumpang, incident log, dan data perjalanan aktual.

---
