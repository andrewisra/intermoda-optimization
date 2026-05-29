# Intermodal AI System - DKI Jakarta

Prototype untuk **AI Open Innovation Challenge 2026 - Case 2: Public Transit Optimization and Intermodal Connectivity**.

Sistem ini menunjukkan cara kerja **AI-Based Intermodal Transit Synchronization System**: ETA, kepadatan, waktu jalan kaki antarmoda, dwell-time decision, incident-aware adjustment, safe speed recommendation, API backend, dan dashboard operator.

---

## 1. Fitur yang Sudah Tersedia

- **ETA baseline** berbasis jadwal/static GTFS atau data demo.
- **ETA delay correction model** dengan RandomForest untuk menunjukkan komponen AI/ML.
- **Transfer optimizer** dengan target waiting time < 8 menit.
- **Dwell time recommendation** untuk menentukan apakah moda non-rel perlu menahan keberangkatan.
- **Walking time antarmoda** dari halte/stasiun asal ke simpul transit tujuan.
- **Synthetic tap-in/tap-out density** untuk estimasi kepadatan halte/stasiun.
- **Load factor recommendation** untuk pemerataan distribusi penumpang.
- **Safe speed adjustment** agar rekomendasi kecepatan tetap dalam batas aman.
- **Driver/operator incident report** untuk banjir, macet, kecelakaan, atau gangguan layanan.
- **FastAPI backend** untuk integrasi aplikasi/website.
- **Streamlit dashboard** untuk demo operator.
- **Excel halte importer** untuk memasukkan daftar halte dari file spreadsheet.
- **Dockerfile dan docker-compose** untuk deployment cepat.

---

## 2. Struktur Project

```text
intermodal_ai_system/
  backend/app/             FastAPI backend
  frontend/dashboard/      Streamlit dashboard
  src/data_pipeline/       generator data, parser GTFS, importer Excel halte
  src/eta/                 baseline ETA dan ML delay correction
  src/density/             tap-in density dan load factor
  src/optimizer/           transfer, dwell time, speed adjustment
  src/incident/            incident reporting
  src/simulator/           simulasi transfer antarmoda
  data/raw/                input data mentah/demo
  data/processed/          data siap pakai aplikasi
  docs/                    mapping proposal, contoh request API
  scripts/                 bootstrap dan runner
  tests/                   unit tests
```

---

## 3. Setup Lokal

### Mac/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 4. Generate Data Demo

Jalankan:

```bash
python scripts/bootstrap_demo.py
```

Script ini membuat data demo di `data/raw` dan `data/processed`:

- `stops.csv`
- `routes.csv`
- `stop_times.csv`
- `schedules.csv`
- `transfer_nodes.csv`
- `fleet_capacity.csv`
- `vehicle_positions.csv`
- `synthetic_tapin.csv`
- `incidents.csv`
- `eta_delay_model.pkl`

Data demo sengaja dibuat kecil agar mudah dipresentasikan, tetapi modulnya sudah siap diganti dengan GTFS, GPS, AFC tap-in/tap-out, dan incident log produksi.

---

## 5. Jalankan API

```bash
uvicorn backend.app.main:app --reload
```

Buka dokumentasi otomatis:

```text
http://127.0.0.1:8000/docs
```

Endpoint utama:

```text
GET  /                    health check
GET  /eta/next            ETA terdekat di halte/stasiun tertentu
GET  /eta/arrivals        daftar arrival berikutnya
POST /optimizer/transfer  rekomendasi transfer antarmoda
GET  /optimizer/simulate-all simulasi semua transfer node
POST /optimizer/speed     rekomendasi penyesuaian kecepatan aman
GET  /density/stop        kepadatan satu halte/stasiun
GET  /density/by-stop     ringkasan kepadatan banyak halte
POST /incidents/report    laporan insiden dari driver/operator
GET  /incidents/active    daftar insiden aktif
```

Contoh request transfer optimizer:

```bash
curl -X POST http://127.0.0.1:8000/optimizer/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_stop_id": "TJ_DUKUH_ATAS",
    "to_stop_id": "MRT_DUKUH_ATAS",
    "current_time": "2026-05-23T07:20:00",
    "first_mode_eta_minutes": 5,
    "load_factor": 0.75
  }'
```

Output contoh:

```json
{
  "from_stop_id": "TJ_DUKUH_ATAS",
  "to_stop_id": "MRT_DUKUH_ATAS",
  "first_mode_eta_minutes": 5,
  "walking_time_minutes": 5.0,
  "decision": {
    "decision": "connect",
    "waiting_time_minutes": 4.0,
    "message": "Koneksi antarmoda feasible. Waiting time masih di bawah threshold."
  }
}
```

---

## 6. Jalankan Dashboard

```bash
streamlit run frontend/dashboard/app.py
```

Dashboard menampilkan:

- KPI walking time, waiting time, density, dan keputusan sistem.
- Peta halte/stasiun demo.
- Peta insiden.
- Simulasi semua transfer node.
- Form laporan insiden.
- Rekomendasi safe speed adjustment.

---

## 7. Import Excel Halte Transjakarta

Letakkan file Excel di `data/raw`, lalu jalankan:

```bash
python -m src.data_pipeline.import_halte_excel --path "data/raw/Daftar_Halte_BRT_Transjakarta_31_Rute_revisi.xlsx"
```

Output:

```text
data/processed/halte_transjakarta_normalized.csv
```

Script akan mencoba membaca kolom seperti `nama halte`, `id halte`, `latitude`, `longitude`, dan `rute`. Bila nama kolom berbeda, script tetap membuat `stop_id` otomatis.

---

## 8. Memakai GTFS Asli

Jika sudah punya GTFS Transjakarta:

1. Ekstrak ZIP GTFS ke:

```text
data/raw/gtfs_transjakarta/
```

2. Pastikan file ini ada:

```text
stops.txt
routes.txt
trips.txt
stop_times.txt
```

3. Jalankan:

```bash
python -m src.data_pipeline.parse_gtfs
```

Untuk MVP lomba, data demo sudah cukup untuk membuktikan logika closed-loop optimizer.

---

## 9. Jalankan Test

```bash
python -m pytest -q
```

Atau:

```bash
make test
```

---

## 10. Docker

```bash
docker compose up --build
```

API:

```text
http://127.0.0.1:8000/docs
```

Dashboard:

```text
http://127.0.0.1:8501
```

---

## 11. Alur Demo yang Disarankan

1. Jalankan `python scripts/bootstrap_demo.py`.
2. Jalankan API dan dashboard.
3. Pilih transfer node `TJ_DUKUH_ATAS -> MRT_DUKUH_ATAS`.
4. Tampilkan ETA moda pertama, walking time, arrival moda kedua, dan waiting time.
5. Ubah delay atau load factor untuk menunjukkan perubahan rekomendasi.
6. Tambahkan laporan insiden untuk menunjukkan incident-aware update.
7. Tampilkan endpoint API `/docs` sebagai bukti integrasi app/website.

---

## 12. Data Produksi yang Dibutuhkan

Prototype ini memakai public/synthetic data. Untuk produksi, data yang perlu diminta lewat MoU/API:

- AFC tap-in/tap-out anonymized.
- AVL/GPS kendaraan.
- Actual schedule log.
- Fleet registry dan kapasitas armada.
- Incident log.
- Service alert.
- Occupancy/crowding.

Prinsip keamanan data:

- tidak menyimpan nomor kartu asli;
- menggunakan `hashed_card_id`;
- dashboard publik hanya agregat;
- akses raw transaction diaudit;
- model training memakai anonymized event stream;
- retention policy harus jelas.

---

## 13. Mapping ke Proposal

Lihat:

```text
docs/PROPOSAL_CODE_MAPPING.md
```

File tersebut menjelaskan bagian proposal mana yang sudah didukung oleh kode prototype.
