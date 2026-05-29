
# Case 2 Data Deep Search - Public Transit Optimization

Tanggal riset: 2026-05-23  
Konteks repo: `case2_public_transit_optimization.md`, `Draft Proposal AI Open - Traffic Management.md`, `Brief Context.md`  
Metode: Exa MCP deep research, Exa web search/crawling, web search resmi, dan cross-check dengan publikasi lokal BPS di `ingfo/`.

## 1. Executive Summary

Case 2 membutuhkan solusi AI untuk ETA, optimasi jadwal, prediksi kepadatan, dashboard, dan simulator konektivitas intermoda. Dari hasil deep search, data yang paling menentukan bukan hanya "jumlah penumpang", tetapi gabungan dari data demand, supply, real-time operasi, dan gangguan eksternal.

Temuan terpenting:

1. **Data tap-in/tap-out granular adalah data P0**, tetapi tidak ditemukan sebagai dataset resmi terbuka. Data ini kemungkinan berada di JakLingko, operator, bank/payment gateway, atau sistem validasi tiket seperti TapConnect. Dataset publik hanya muncul sebagai contoh skema/riset, bukan sumber resmi operasional.
2. **Data kapasitas armada harus dipisah menjadi dua lapis**: jumlah armada aktif dan kapasitas per jenis kendaraan/trainset. Jumlah armada agregat relatif tersedia dari laporan resmi/BPS, tetapi kapasitas per vehicle type, alokasi per rute, status aktif, dan depot hampir pasti butuh akses operator.
3. **GTFS Transjakarta adalah data publik paling siap pakai** untuk baseline network, stop, route, shape, trip, dan schedule. Ini dapat langsung dipakai untuk prototype ETA dan simulator Transjakarta.
4. **GTFS static dan GTFS-Realtime untuk MRT, LRT Jakarta, KRL/KAI Commuter, dan JakLingko tidak ditemukan sebagai feed publik resmi**. Untuk optimasi intermoda penuh, data jadwal aktual dan vehicle position harus diminta lewat MoU/API.
5. **Data trafik, banjir, cuaca, dan insiden objektif penting** karena ETA bus sangat dipengaruhi delay jalan, sinyal ATCS/ITCS, banjir/genangan, cuaca ekstrem, dan road closure.

## 2. Prioritas Data Untuk Case 2

| Prioritas | Dataset | Kenapa penting | Status akses | Sumber terbaik |
|---|---|---|---|---|
| P0 | Tap-in/tap-out AFC per transaksi | Demand real, OD matrix, transfer chain, kepadatan halte/stasiun, validasi simulator | Restricted/operator | JakLingko/TapConnect/operator; contoh skema publik di GitHub dan riset LRT |
| P0 | Vehicle GPS/AVL atau GTFS-Realtime | ETA real-time, headway monitoring, bunching detection, delay prediction | Mostly restricted | Operator, Transitland/API aggregator jika tersedia |
| P0 | Static GTFS/schedule/route/stop/shape | Network graph, scheduled ETA, transfer time, simulator baseline | Transjakarta public; mode lain belum ditemukan public | Official Transjakarta GTFS |
| P0 | Fleet capacity and allocation | Supply capacity, load factor, armada needed, optimization constraint | Agregat public; detail restricted | Annual reports, BPS, operator fleet registry |
| P1 | Passenger count aggregate | Baseline demand, trend, seasonality, KPI dashboard | Public/agregat | Satu Data/Data.go.id, BPS, annual reports |
| P1 | Actual vs scheduled trips/headway | Reliability model, schedule optimization, missed trip detection | Restricted | Operator control center |
| P1 | Traffic speed, ATCS/ITCS, junction delay | Bus ETA and route delay correction | Partial public; live restricted | TUMI/Dishub, Jakarta ITCS, Google/Dishub |
| P1 | Weather, rainfall, flood, water level | Delay risk, route disruption, rerouting | Public to partial public | PetaBencana, BMKG MEWS, BPBD |
| P1 | Incident and disruption logs | Service alerts, root cause delay, dashboard | Restricted/partial public | Operator, Dishub, BPBD, JAKI/CRM |
| P2 | Walking network and transfer nodes | Door-to-door multimodal routing and transfer penalty | Public via OSM plus field validation | OpenStreetMap, station/halte maps |
| P2 | Fare/payment integration metadata | Intermodal user journey and transfer behavior | Public docs; raw events restricted | JakLingko, KMT, QRIS Tap, TapConnect |
| P2 | User complaint/driver report text | Early warning and service quality insight | Restricted | CRM, JAKI, operator reports |

## 3. Data Public Yang Langsung Bisa Dipakai

### 3.1 Transjakarta GTFS Static

**Sumber utama**

- Official GTFS ZIP: [gtfs.transjakarta.co.id/files/file_gtfs.zip](https://gtfs.transjakarta.co.id/files/file_gtfs.zip)
- Metadata Transitland: [Transitland - PT Transportasi Jakarta GTFS feed](https://www.transit.land/feeds/f-transjakarta~id)
- PPID Transjakarta berkala: [ppid.transjakarta.co.id/informasi/berkala](https://ppid.transjakarta.co.id/informasi/berkala)
- BusMaps mirror/metadata: [BusMaps - Transportasi Jakarta GTFS](https://busmaps.com/en/indonesia/Transportasi-Jakarta/pt-transportasi)

**Isi umum**

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `shapes.txt`
- `calendar.txt` atau `calendar_dates.txt`
- fare files jika tersedia

**Kegunaan untuk Case 2**

- Build graph halte-rute.
- Baseline ETA terjadwal.
- Simulasi headway dan transfer.
- Peta dashboard rute/halte.
- Seed schedule optimization sebelum data real-time tersedia.

**Catatan kualitas**

Feed ini wajib diunduh dan di-parse dalam prototype. Saat dicek via web, file resmi tersedia sebagai ZIP dan berukuran sekitar 5.3 MB dengan pembaruan 2026 pada metadata HTTP. Validasi versi tetap perlu dilakukan saat pipeline berjalan.

### 3.2 Dataset Halte, Rute, Trayek, dan Penumpang Transjakarta

**Sumber**

- [Data Halte Transjakarta - data.go.id](https://data.go.id/dataset/dataset/data-halte-transjakarta)
- [Data Jumlah Penumpang Transjakarta - data.go.id](https://data.go.id/dataset/dataset/data-jumlah-penumpang-transjakarta)
- [Data Rute Jalur Transjakarta - data.go.id](https://data.go.id/dataset/dataset/data-rute-jalur-transjakarta)
- [Data Trayek Bus Transjakarta - data.go.id](https://data.go.id/dataset/dataset/data-trayek-bus-transjakarta)

**Kegunaan**

- Baseline demand agregat.
- Validasi jumlah halte/rute dari GTFS.
- Dashboard historis passenger count.
- Input awal density model jika tap-in granular belum tersedia.

**Limitasi**

Data agregat tidak cukup untuk membentuk OD matrix per jam, prediksi kepadatan per halte, atau transfer chain lintas moda. Untuk itu tetap perlu tap-in/tap-out event logs.

### 3.3 Kendaraan dan Trayek Angkutan Umum

**Sumber**

- [Data Jumlah Kendaraan dan Trayek Angkutan Umum DKI Jakarta - data.go.id](https://data.go.id/dataset/dataset/data-jumlah-kendaraan-dan-trayek-angkutan-umum-dki-jakarta)
- [Kendaraan Angkutan Umum yang Terintegrasi Tahun 2022 - data.go.id](https://data.go.id/dataset/dataset/kendaraan-angkutan-umum-yang-terintegrasi-tahun-2022)
- [Cakupan Layanan Angkutan Umum - data.go.id](https://data.go.id/dataset/dataset/cakupan-layanan-angkutan-umum)

**Kegunaan**

- Fleet supply baseline.
- Constraint awal untuk simulator.
- Cakupan layanan untuk analisis akses 500 meter dari angkutan umum.
- Identifikasi rute/wilayah undersupply.

**Limitasi**

Dataset publik cenderung agregat. Untuk optimasi operasional, dibutuhkan registry armada aktual:

- `vehicle_id`
- `operator`
- `mode`
- `route_id`
- `vehicle_type`
- `seated_capacity`
- `standing_capacity`
- `total_capacity`
- `depot`
- `status_active`
- `shift_start`
- `shift_end`
- `maintenance_status`

### 3.4 BPS Statistik Transportasi DKI Jakarta

**Sumber**

- [BPS - Transportation Statistics of DKI Jakarta Province 2023](https://jakarta.bps.go.id/en/publication/2024/11/25/c379c24fabcc3a9616cf246e/transportation-statistics-of-dki-jakarta-province-2023.html)
- File lokal: `ingfo/statistik-transportasi-provinsi-dki-jakarta-2023.pdf`
- Contoh rilis bulanan: [BPS DKI Jakarta - Perkembangan Transportasi Desember 2024](https://jakarta.bps.go.id/id/pressrelease/2025/02/03/1196/perkembangan-transportasi-dki-jakarta-desember-2024.html)

**Angka penting dari publikasi 2023 di repo**

| Moda | Data 2023 yang relevan |
|---|---|
| Transjakarta | 284.92 juta penumpang; rata-rata 23.74 juta/bulan; puncak Oktober 29.15 juta; 4,514 bus |
| KRL Jabodetabek | 290.89 juta penumpang; 1,042 unit KRL; 1,090 perjalanan/hari |
| MRT Jakarta | 33.45 juta penumpang; naik sekitar 69 persen YoY |
| LRT Jakarta | 1.027 juta penumpang; naik sekitar 49.92 persen YoY |

**Kegunaan**

- Validasi besaran demand lintas moda.
- KPI baseline untuk proposal.
- Input seasonality dan trend tahunan.

**Limitasi**

BPS bagus untuk baseline makro, tetapi tidak cukup untuk ETA, headway real-time, OD matrix, dan kepadatan per jam.

## 4. Operator and Official Reports

### 4.1 Transjakarta

**Sumber**

- [Laporan kinerja 2024 Transjakarta](https://transjakarta.co.id/berita/laporan-kinerja-2024-sepanjang-tahun-2024-transjakarta-tumbuh-tinggi-dan-semakin-efisien)
- [PPID Transjakarta - Laporan Tahunan](https://ppid.transjakarta.co.id/informasi/laporan-tahunan-transjakarta)
- [ANTARA - Pelanggan Transjakarta capai 371 juta pelanggan di 2024](https://www.antaranews.com/berita/4630905/pelanggan-transjakarta-capai-371-juta-pelanggan-di-2024)
- [ANTARA - Produktivitas operasional Transjakarta 2023](https://www.antaranews.com/berita/4261231/produktivitas-operasional-dan-kepuasan-konsumen-transjakarta-meningkat)

**Angka penting**

| Tahun | Penumpang | Armada/rute | Catatan |
|---|---:|---:|---|
| 2023 | 284.9 juta | 4,355 armada; 246 rute menurut ANTARA/Transjakarta | IKP 4.42/5; subsidi per penumpang Rp11,474 |
| 2024 | 371.4 juta lebih | 4,388 armada; 242 rute | Coverage 91.7 persen; app TJ 540 ribu user; 300 bus listrik |

**Kegunaan untuk Case 2**

- Narasi urgensi skala demand.
- Baseline kapasitas supply.
- KPI sebelum-sesudah optimasi.
- Justifikasi dashboard kepadatan dan reliability.

**Gap**

Belum cukup untuk mengetahui kapasitas per armada dan alokasi real-time per rute. Untuk simulator, data wajib diminta ke operator.

### 4.2 MRT Jakarta

**Sumber**

- [MRT Jakarta Annual Report 2024](https://jakartamrt.co.id/id/annual-report/mrt-jakarta-annual-report-2024)
- [MRT Jakarta target 50 juta pelanggan 2026](https://jakartamrt.co.id/id/info-terkini/pt-mrt-jakarta-perseroda-targetkan-50-juta-pelanggan-pada-2026)
- [MRT Jakarta tengah tahun 2024](https://www.jakartamrt.co.id/id/info-terkini/tengah-tahun-2024-184-juta-orang-gunakan-mrt-jakarta)

**Angka penting**

| Periode | Ridership |
|---|---:|
| 2023 | Sekitar 33.5 juta penumpang |
| Jan-Jun 2024 | 18.49 juta penumpang; rata-rata 101,581/hari |
| 2025 | 46.45 juta penumpang; rata-rata 127,259/hari |
| Target 2026 | 50 juta/tahun; sekitar 137 ribu/hari |

**Kegunaan**

- Integrasi intermoda di stasiun transit.
- Transfer demand antara MRT-Transjakarta-KRL.
- Validasi feeder contribution, terutama karena MRT menyebut kontribusi feeder sekitar 22-23 persen pada beberapa rilis.

**Gap**

Perlu data trainset, kapasitas per rangkaian, jadwal aktual, platform crowding, entry-exit station by hour, dan transfer count.

### 4.3 LRT Jakarta

**Sumber**

- [LRT Jakarta - Laporan Tahunan](https://server.lrtjakarta.co.id/laporan.html)
- [BPS - Jumlah Penumpang LRT Jakarta](https://jakarta.bps.go.id/id/statistics-table/2/MTMyMCMy/jumlah-penumpang-light-rail-transit--lrt--jakarta.html)
- [BPS DKI - Perkembangan Transportasi Desember 2024](https://jakarta.bps.go.id/id/pressrelease/2025/02/03/1196/perkembangan-transportasi-dki-jakarta-desember-2024.html)
- [Riset OD smart card LRT Jakarta](https://journal2.upgris.ac.id/index.php/asset/article/download/2254/967)
- [Riset pola operasi dan kebutuhan sarana LRT Jakarta](https://dinastires.org/JAFM/article/download/3133/2184)

**Angka dan insight penting**

| Data | Nilai/insight | Catatan |
|---|---:|---|
| Ridership 2023 | 1.027 juta penumpang | Dari publikasi BPS lokal |
| Desember 2024 | 101,209 penumpang; 6,360 perjalanan | Dari rilis BPS |
| Riset OD Jan-Feb 2025 | 185,512 trip records | Riset, bukan dataset publik resmi |
| Skenario kapasitas riset | 270 penumpang per trainset 2-car; 540 per 4-car | Gunakan sebagai asumsi sementara, perlu validasi operator |

**Kegunaan**

- Model OD stasiun.
- Transfer simulation untuk koridor Kelapa Gading-Velodrome dan integrasi lanjutan.
- Kapasitas rail feeder dalam simulator.

**Gap**

Raw AFC, schedule aktual, platform crowding, dan rolling stock registry perlu akses operator.

### 4.4 KAI Commuter / KRL

**Sumber**

- [KAI Commuter Annual Report PDF](https://kci.id/files/download/annual_report/AR%20KCI%2019082024%20LR%20-%20LK%20under%2010MB.pdf)
- [Merdeka - pengguna KRL 2024](https://www.merdeka.com/uang/ternyata-pengguna-krl-sepanjang-tahun-2024-mencapai-374-juta-orang-paling-banyak-di-jabodetabek-295565-mvk.html)
- [Bisnis - proyeksi penumpang KRL 2025](https://ekonomi.bisnis.com/read/20250131/98/1835667/penumpang-krl-diprediksi-tembus-383-juta-orang-sepanjang-2025)
- [ANTARA - pengguna Commuter Line akhir 2024](https://megapolitan.antaranews.com/berita/332118/ada-12-juta-pengguna-commuter-line-pada-akhir-tahun-2024)

**Angka penting**

| Periode | Data |
|---|---|
| 2023 | Jabodetabek 290.89 juta penumpang; 1,090 perjalanan/hari; 1,042 unit KRL menurut BPS |
| 2024 | Media mengutip total pengguna KAI Commuter sekitar 374 juta dan Jabodetabek sekitar 328 juta |
| 2025 projection | Media mengutip target/proyeksi sekitar 383.8 juta total pengguna |

**Kegunaan**

- Intermodal demand terbesar di Jabodetabek.
- Transfer node utama: Manggarai, Tanah Abang, Duri, Sudirman/Dukuh Atas, Kampung Bandan, dan lainnya.
- Constraint penting untuk jadwal feeder bus.

**Gap**

GTFS static/RT publik resmi tidak ditemukan. Perlu data jadwal, trip actual, platform crowding, trainset capacity, dan AFC OD dari KAI Commuter.

## 5. Tap-in/Tap-out Data

### 5.1 Kenapa Tap-in/Tap-out P0

Tap-in/tap-out adalah data paling kuat untuk menjawab:

- asal-tujuan perjalanan;
- waktu puncak per halte/stasiun;
- transfer antarmoda;
- estimasi kepadatan dalam kendaraan;
- missed connection;
- perubahan demand setelah optimasi jadwal;
- demand forecasting per rute/jam/hari.

Tanpa data ini, sistem hanya dapat membangun demand model dari agregat, yang biasanya lemah untuk keputusan rute dan headway.

### 5.2 Skema Ideal Yang Perlu Diminta

| Field | Deskripsi |
|---|---|
| `event_id` | ID transaksi unik |
| `hashed_card_id` | ID kartu/user yang sudah di-hash dan salted |
| `mode` | Transjakarta, MRT, LRT, KRL, JakLingko feeder |
| `operator` | Operator layanan |
| `route_id` | ID rute jika tersedia |
| `trip_id` | ID trip jika bisa dikaitkan dengan schedule/AVL |
| `tap_in_stop_id` | Halte/stasiun masuk |
| `tap_in_time` | Timestamp masuk |
| `tap_out_stop_id` | Halte/stasiun keluar |
| `tap_out_time` | Timestamp keluar |
| `payment_channel` | Kartu bank, KMT, QRIS Tap, aplikasi, dan lain-lain |
| `fare_product` | Jenis tiket/tarif tanpa detail sensitif |
| `transfer_flag` | Apakah bagian dari perjalanan transfer |
| `validation_status` | Valid, failed, reversed, manual adjustment |

### 5.3 Sumber Publik Sebagai Bukti/Proxy

| Sumber | Isi | Status |
|---|---|---|
| [GitHub Capstone Purwadhika - Transjakarta.csv](https://github.com/Hunafarizal/Capstone_Purwadhika_2) | Contoh dataset tap-in/tap-out Transjakarta April 2023 dengan field halte, timestamp, corridor, dan atribut kartu | Bukan official; gunakan hanya sebagai contoh skema dan dummy/proxy |
| [Riset OD smart card LRT Jakarta](https://journal2.upgris.ac.id/index.php/asset/article/download/2254/967) | Studi OD matrix dari AFC LRT Jakarta Jan-Feb 2025, 185,512 trip records | Riset publik; raw dataset tidak terbuka |
| [JakLingko - tap in/tap out one time payment](https://www.jaklingkoindonesia.co.id/en/newsroom/article/jakinfo/53/jaklingko-ensures-that-transjakarta-tap-in-tap-out-is-one-time-payment) | Konfirmasi sistem tap-in/tap-out dan integrasi pembayaran | Public info; bukan raw data |
| [TapConnect Booking API](https://documentation.tapconnect.io/booking-api) | Dokumentasi API booking/leg/payment event | Butuh token/API key |
| [TapConnect TOMP API](https://documentation.tapconnect.io/tomp-api/) | API interoperabilitas mobility booking/legs/events | Butuh token/API key |
| [TapConnect Validation API](https://documentation.tapconnect.io/validation-api/) | Jalur teknis validasi event tiket | Butuh token/API key |
| [KCI - KMT integration](https://kci.id/informasi-publik/berita/kembangkan-integrasi-sistem-pembayaran-kai-commuter-gandeng-bus-metro-jabar-trans-permudah-transaksi-pembayaran-tiket-dengan-kartu-multi-trip) | KMT dapat digunakan lintas layanan seperti LRT, MRT, Transjakarta, dan lainnya | Bukti integrasi pembayaran, bukan data event |
| [CNN Indonesia - QRIS Tap KRL/Transjakarta/MRT/LRT](https://www.cnnindonesia.com/edukasi/20251104100932-561-1291591/cara-pakai-qris-tap-naik-krl-transjakarta-mrt-dan-lrt) | Mekanisme QRIS Tap untuk beberapa moda | Public-facing payment flow |

### 5.4 Privacy Guardrail

Data tap-in sangat sensitif. Untuk proposal, tuliskan bahwa sistem tidak membutuhkan data identitas mentah.

Minimal privacy rule:

- jangan simpan nomor kartu asli;
- jangan simpan nama pemegang kartu;
- jangan simpan tanggal lahir mentah;
- gunakan `hashed_card_id` dengan salt yang dikelola pemilik data;
- gunakan age bin jika demografi diperlukan;
- lakukan aggregation threshold, misalnya tidak menampilkan OD dengan jumlah sangat kecil;
- pisahkan raw event lake dari public dashboard;
- audit akses untuk data level transaksi.

## 6. Armada dan Kapasitas

### 6.1 Kenapa Kapasitas Armada P0

Schedule optimization tidak cukup hanya tahu demand. Model juga harus tahu supply:

- berapa kendaraan tersedia;
- kapasitas tiap kendaraan/trainset;
- alokasi kendaraan ke rute;
- status aktif/maintenance;
- headway aktual;
- trip cancellation;
- deadhead/depot constraint.

Tanpa kapasitas armada, simulator dapat memberi rekomendasi headway yang tidak feasible.

### 6.2 Data Armada Yang Ditemukan

| Moda | Data publik yang ditemukan | Sumber |
|---|---|---|
| Transjakarta | 2024: 4,388 armada, 242 rute, 371.4 juta pelanggan; 300 bus listrik | [Transjakarta 2024](https://transjakarta.co.id/berita/laporan-kinerja-2024-sepanjang-tahun-2024-transjakarta-tumbuh-tinggi-dan-semakin-efisien) |
| Transjakarta | 2023: 284.92 juta penumpang; 4,514 bus dalam publikasi BPS | [BPS 2023](https://jakarta.bps.go.id/en/publication/2024/11/25/c379c24fabcc3a9616cf246e/transportation-statistics-of-dki-jakarta-province-2023.html) |
| Transjakarta | Feb 2024: 28.5 juta penumpang; 4,456 armada menurut rilis BPS | [BPS Feb 2024](https://jakarta.bps.go.id/id/pressrelease/2024/04/01/1179/perkembangan-transportasi-provinsi-dki-jakarta-februari-2024.html) |
| MRT Jakarta | 2025: 46.45 juta pelanggan; rata-rata 127,259/hari | [MRT Jakarta 2026 target](https://jakartamrt.co.id/id/info-terkini/pt-mrt-jakarta-perseroda-targetkan-50-juta-pelanggan-pada-2026) |
| LRT Jakarta | Riset: skenario kapasitas 270 pax/trainset 2-car dan 540 pax/trainset 4-car | [Riset kebutuhan sarana LRT](https://dinastires.org/JAFM/article/download/3133/2184) |
| KRL Jabodetabek | 2023: 1,042 unit KRL; 1,090 perjalanan/hari; 290.89 juta penumpang Jabodetabek | BPS 2023 lokal dan [KAI Commuter annual report](https://kci.id/files/download/annual_report/AR%20KCI%2019082024%20LR%20-%20LK%20under%2010MB.pdf) |

### 6.3 Data Armada Yang Harus Diminta Ke Operator

| Field | Fungsi dalam model |
|---|---|
| `vehicle_id` atau `trainset_id` | Identitas armada dalam trip log |
| `vehicle_type` | Single bus, articulated bus, low entry bus, microtrans, trainset type |
| `seated_capacity` | Kapasitas duduk |
| `standing_capacity` | Kapasitas berdiri |
| `total_capacity` | Constraint load factor |
| `route_assignment` | Alokasi rute per jam/hari |
| `depot_id` | Constraint dispatch dan deadhead |
| `active_status` | Armada siap operasi |
| `maintenance_status` | Ketersediaan supply |
| `gps_device_status` | Kualitas ETA data |
| `occupancy_sensor_available` | Apakah bisa estimasi kepadatan real-time |

### 6.4 Asumsi Prototype Jika Data Detail Belum Ada

Untuk demo, gunakan pendekatan bertingkat:

1. Ambil jumlah armada agregat dari BPS/laporan tahunan.
2. Gunakan GTFS trip count untuk mengestimasi supply per rute.
3. Assign kapasitas generik per vehicle type dengan sensitivity analysis.
4. Validasi load factor menggunakan ridership agregat dan sampel tap-in proxy.
5. Tandai semua output sebagai "scenario simulator", bukan keputusan operasional final.

## 7. Data Trafik, Cuaca, Banjir, dan Insiden

### 7.1 Traffic and ATCS

**Sumber**

- [TUMI Datahub - Traffic Recap Data in DKI Jakarta](https://hub.tumidata.org/dataset/traffic_recap_data_in_dki_jakarta_jakarta)
- [Jakarta.go.id - AI/ITCS solusi urai kemacetan](https://www.jakarta.go.id/page/artificial-intelligence-solusi-urai-kemacetan-jakarta)
- [Jakarta Smart City Tableau case](https://www.tableau.com/solutions/customer/jakarta-smart-city-visualizes-solutions-urban-challenges)

**Kegunaan**

- ETA correction untuk bus.
- Delay by corridor/intersection.
- Deteksi dampak sinyal dan kemacetan.
- Dashboard traffic-aware transit performance.

**Gap**

Traffic recap publik tidak sama dengan live speed feed. Untuk live ETA, perlu salah satu:

- live AVL/GPS dari bus;
- Google/Waze/ITCS travel time;
- ATCS signal timing;
- CCTV-derived speed/queue length;
- API internal Dishub/Jakarta Smart City.

### 7.2 CCTV and Passenger Density

**Sumber**

- [GitHub DSSG/Jakarta Smart City traffic safety public](https://github.com/dssg/jakarta_smart_city_traffic_safety_public)
- [Kompas - Dishub uji kamera AI hitung penumpang Transjabodetabek](https://megapolitan.kompas.com/read/2025/08/21/16405441/dishub-uji-coba-kamera-ai-hitung-jumlah-penumpang-transjabodetabek)
- [Media Indonesia - 27,000 CCTV Jakarta real-time](https://mediaindonesia.com/megapolitan/891389/27000-cctv-jakarta-akan-awasi-kota-real-time)

**Kegunaan**

- Estimasi occupancy jika tap data telat/tidak lengkap.
- Incident detection.
- Validasi antrean halte/stasiun.

**Gap**

Raw CCTV stream bukan dataset publik umum. Untuk proposal, posisikan sebagai optional enterprise integration, bukan asumsi wajib prototype.

### 7.3 Weather, Flood, and Water Level

**Sumber**

- [PetaBencana API - floodgauges](https://docs.petabencana.id/routes/pemantauan-tma)
- [PetaBencana API - floods](https://docs.petabencana.id/routes/area-banjir)
- [BMKG ArcGIS REST MEWS](https://dashboard-signature.bmkg.go.id/server/rest/services/MEWS)
- [BMKG SACA&D publications](https://sacad.bmkg.go.id/publications/index.php)
- [BPBD DKI Jakarta](https://bpbd.jakarta.go.id)

**Kegunaan**

- Delay prediction saat hujan/genangan.
- Rerouting dan service alert.
- Incident-aware ETA.
- Scenario simulator untuk banjir.

**Contoh endpoint PetaBencana**

- Flood gauges Jakarta: `https://data.petabencana.id/floodgauges?admin=ID-JK`
- Flood affected areas Jakarta: `https://data.petabencana.id/floods?admin=ID-JK&minimum_state=1`

## 8. Dataset Tambahan Yang Objectively Penting

Berikut data yang tidak selalu disebut eksplisit dalam case, tetapi secara objektif penting agar solusi benar-benar bekerja.

| Dataset | Dampak langsung | Sumber/akses |
|---|---|---|
| Stop/station geometry dengan entrance/exit | Transfer walking time dan catchment area | GTFS, operator station maps, OSM |
| Pedestrian network | Door-to-door route dan transfer penalty | OpenStreetMap, field validation |
| Fare rules and transfer rules | Simulasi rute realistis dan affordability | GTFS fare files, JakLingko docs |
| Real-time service alert | ETA dan rerouting saat gangguan | GTFS-RT alerts/operator |
| Trip cancellation log | Reliability KPI dan schedule optimizer | Operator |
| Dwell time per stop | ETA dan kepadatan boarding/alighting | AVL + AFC/operator |
| Bus lane availability and road segment priority | ETA bus vs mixed traffic | Dishub/operator GIS |
| Depot and charging infrastructure | Feasibility bus dispatch, terutama e-bus | Transjakarta/operator |
| School/event calendar | Demand spike forecast | Dinas Pendidikan, tourism/event APIs/manual calendar |
| Holidays and long weekend | Ridership anomaly | Kalender nasional |
| Road closure/construction | Incident-aware routing | Dishub, police, JAKI |
| Complaint text and driver reports | Early-warning incident detection | JAKI/CRM/operator |
| Accessibility data | Inclusive routing and station usability | Operator, field survey |

## 9. Minimum Dataset Untuk Prototype

Prototype yang realistis dapat dibuat dengan kombinasi open data dan data sintetis terkontrol:

| Modul | Minimum data |
|---|---|
| ETA baseline | Transjakarta GTFS static, route shape, stop times |
| ETA adjustment | Historical speed proxy, traffic recap, weather/flood flags |
| Density prediction | Ridership aggregate, synthetic tap-in/tap-out based on public schema, GTFS stop sequence |
| Schedule optimization | GTFS trips, assumed fleet capacity, headway constraints |
| Intermodal transfer | GTFS Transjakarta, manually curated MRT/LRT/KRL station nodes, walking distance from OSM |
| Dashboard | Ridership KPI, fleet KPI, ETA reliability, hotspot stops, disruption map |
| Simulator | Demand scenarios, fleet capacity assumptions, disruption scenarios |

Untuk proposal, jelaskan dengan tegas bahwa prototype bisa memakai public + synthetic/anonymized sample, sedangkan deployment produksi membutuhkan MoU data operator.

## 10. Data Request Checklist Untuk MoU/API

### 10.1 Ke Dishub DKI/JakLingko/Operator

Minta data dengan format terstandar:

| Paket data | Field utama |
|---|---|
| AFC tap-in/tap-out | hashed card ID, mode, route, stop/station, timestamp, payment channel, transfer flag |
| AVL/GPS | vehicle ID, timestamp, lat/lon, speed, heading, route, trip, occupancy jika ada |
| Schedule actual | planned departure, actual departure, planned arrival, actual arrival, cancellation, delay reason |
| Fleet registry | vehicle/trainset ID, type, capacity, depot, status, maintenance |
| Incident log | timestamp, location, route affected, severity, reason, recovery time |
| Service alert | route, stop, start/end time, user-facing message |
| Crowd/occupancy | stop queue estimate, vehicle load factor, platform crowding |

### 10.2 Data Governance

Syarat yang sebaiknya masuk proposal:

- raw PII tidak masuk model;
- card/customer ID harus hashed;
- data sharing menggunakan least privilege;
- dashboard publik hanya aggregate;
- model training memakai anonymized event stream;
- retention policy jelas;
- audit log untuk semua akses raw data;
- output rekomendasi operasional harus bisa dijelaskan.

## 11. Mapping Data Ke Output Case 2

| Output Case 2 | Data wajib | Data peningkat akurasi |
|---|---|---|
| Prediksi ETA | GTFS, AVL/GPS, stop sequence | traffic speed, ATCS, weather, flood, incident |
| Optimasi jadwal | GTFS, actual trip logs, fleet capacity, demand by hour | transfer demand, dwell time, depot constraints |
| Prediksi kepadatan | tap-in/tap-out, capacity, route/trip mapping | CCTV occupancy, event calendar, weather |
| Dashboard | KPI ridership, ETA, load factor, incident, map layers | real-time alerts, CCTV-derived density |
| Simulator intermoda | network graph, station/halte nodes, walking links, schedule | fare rules, transfer rules, OD matrix |
| Executive decision support | aggregate ridership, subsidy/KPI, coverage, reliability | scenario impact, equity/accessibility metrics |

## 12. Data Gaps and Risk

| Gap | Risiko jika tidak ada | Mitigasi |
|---|---|---|
| Raw tap-in/tap-out tidak tersedia | Density dan OD model menjadi estimasi kasar | Gunakan proxy/synthetic untuk demo; ajukan MoU untuk production |
| GTFS-RT/AVL tidak tersedia | ETA tidak live dan sulit mendeteksi bunching | Mulai dari scheduled ETA; integrasikan GPS saat akses ada |
| Kapasitas per vehicle type tidak lengkap | Rekomendasi headway bisa tidak feasible | Gunakan range kapasitas dan sensitivity analysis |
| Data mode lain tidak punya GTFS | Intermoda lintas MRT/LRT/KRL kurang presisi | Curate timetable/station graph manual sementara |
| Incident logs tidak terstruktur | Root cause delay lemah | Gunakan service alert, weather/flood, dan manual event annotation |
| Data privacy tidak dijaga | Risiko hukum, reputasi, dan keamanan | Privacy-by-design dan anonymization sejak awal |

## 13. Source Inventory

| Source | URL | Data | Access | Confidence |
|---|---|---|---|---|
| Transjakarta GTFS official | [link](https://gtfs.transjakarta.co.id/files/file_gtfs.zip) | Static GTFS routes/stops/trips/stop times/shapes | Public | High |
| Transitland Transjakarta metadata | [link](https://www.transit.land/feeds/f-transjakarta~id) | Feed metadata and version context | Public | High |
| PPID Transjakarta berkala | [link](https://ppid.transjakarta.co.id/informasi/berkala) | Official information and GTFS reference | Public | High |
| Data Halte Transjakarta | [link](https://data.go.id/dataset/dataset/data-halte-transjakarta) | Stop list/address | Public | High |
| Data Jumlah Penumpang Transjakarta | [link](https://data.go.id/dataset/dataset/data-jumlah-penumpang-transjakarta) | Passenger aggregate | Public | High |
| Data Rute Jalur Transjakarta | [link](https://data.go.id/dataset/dataset/data-rute-jalur-transjakarta) | Route/path data | Public | Medium-high |
| Data Trayek Bus Transjakarta | [link](https://data.go.id/dataset/dataset/data-trayek-bus-transjakarta) | Bus route/trayek data | Public | Medium-high |
| Kendaraan dan trayek angkutan umum | [link](https://data.go.id/dataset/dataset/data-jumlah-kendaraan-dan-trayek-angkutan-umum-dki-jakarta) | Vehicle and route count | Public | Medium |
| Kendaraan terintegrasi 2022 | [link](https://data.go.id/dataset/dataset/kendaraan-angkutan-umum-yang-terintegrasi-tahun-2022) | Integrated public transport vehicles | Public | Medium |
| Cakupan layanan angkutan umum | [link](https://data.go.id/dataset/dataset/cakupan-layanan-angkutan-umum) | Coverage/accessibility metric | Public | Medium |
| Transjakarta 2024 performance | [link](https://transjakarta.co.id/berita/laporan-kinerja-2024-sepanjang-tahun-2024-transjakarta-tumbuh-tinggi-dan-semakin-efisien) | Ridership, fleet, routes, KPI | Public | High |
| PPID annual reports Transjakarta | [link](https://ppid.transjakarta.co.id/informasi/laporan-tahunan-transjakarta) | Annual reports | Public | High |
| BPS DKI Transportation Statistics 2023 | [link](https://jakarta.bps.go.id/en/publication/2024/11/25/c379c24fabcc3a9616cf246e/transportation-statistics-of-dki-jakarta-province-2023.html) | Transport statistics | Public | High |
| BPS transport Dec 2024 | [link](https://jakarta.bps.go.id/id/pressrelease/2025/02/03/1196/perkembangan-transportasi-dki-jakarta-desember-2024.html) | Monthly MRT/LRT/transport stats | Public | High |
| BPS transport Feb 2024 | [link](https://jakarta.bps.go.id/id/pressrelease/2024/04/01/1179/perkembangan-transportasi-provinsi-dki-jakarta-februari-2024.html) | Monthly stats including Transjakarta fleet/passengers | Public | High |
| MRT annual report 2024 | [link](https://jakartamrt.co.id/id/annual-report/mrt-jakarta-annual-report-2024) | Annual report | Public | High |
| MRT 2026 target release | [link](https://jakartamrt.co.id/id/info-terkini/pt-mrt-jakarta-perseroda-targetkan-50-juta-pelanggan-pada-2026) | 2025 ridership and 2026 target | Public | High |
| MRT mid-year 2024 release | [link](https://www.jakartamrt.co.id/id/info-terkini/tengah-tahun-2024-184-juta-orang-gunakan-mrt-jakarta) | Jan-Jun 2024 ridership | Public | High |
| LRT Jakarta annual reports | [link](https://server.lrtjakarta.co.id/laporan.html) | Annual reports | Public | High |
| BPS LRT passenger table | [link](https://jakarta.bps.go.id/id/statistics-table/2/MTMyMCMy/jumlah-penumpang-light-rail-transit--lrt--jakarta.html) | LRT passenger statistics | Public | High |
| KAI Commuter annual report | [link](https://kci.id/files/download/annual_report/AR%20KCI%2019082024%20LR%20-%20LK%20under%2010MB.pdf) | KCI annual report | Public | High |
| TUMI traffic recap | [link](https://hub.tumidata.org/dataset/traffic_recap_data_in_dki_jakarta_jakarta) | ATCS/traffic recap | Public | Medium-high |
| Jakarta ITCS article | [link](https://www.jakarta.go.id/page/artificial-intelligence-solusi-urai-kemacetan-jakarta) | AI traffic control context | Public info | Medium-high |
| Jakarta Smart City Tableau case | [link](https://www.tableau.com/solutions/customer/jakarta-smart-city-visualizes-solutions-urban-challenges) | Dashboard context | Public info | Medium |
| DSSG Jakarta traffic safety GitHub | [link](https://github.com/dssg/jakarta_smart_city_traffic_safety_public) | CCTV traffic analysis pipeline | Public code | Medium |
| PetaBencana floodgauges | [link](https://docs.petabencana.id/routes/pemantauan-tma) | Water-level/flood gauge API | Public API | High |
| PetaBencana floods | [link](https://docs.petabencana.id/routes/area-banjir) | Flood affected area API | Public API | High |
| BMKG MEWS ArcGIS REST | [link](https://dashboard-signature.bmkg.go.id/server/rest/services/MEWS) | Weather/flood map services | Public REST | High |
| BMKG SACA&D | [link](https://sacad.bmkg.go.id/publications/index.php) | Daily gridded climate data context | Public | Medium-high |
| JakLingko tap-in/tap-out info | [link](https://www.jaklingkoindonesia.co.id/en/newsroom/article/jakinfo/53/jaklingko-ensures-that-transjakarta-tap-in-tap-out-is-one-time-payment) | Payment/tap policy info | Public info | Medium-high |
| TapConnect Booking API | [link](https://documentation.tapconnect.io/booking-api) | Booking and payment API docs | Token required | Medium |
| TapConnect TOMP API | [link](https://documentation.tapconnect.io/tomp-api/) | Mobility interoperability API | Token required | Medium |
| TapConnect Validation API | [link](https://documentation.tapconnect.io/validation-api/) | Ticket validation API docs | Token required | Medium |
| GitHub Transjakarta tap sample | [link](https://github.com/Hunafarizal/Capstone_Purwadhika_2) | Example tap-in/tap-out schema | Public but non-official | Low-medium |
| LRT smart card OD research | [link](https://journal2.upgris.ac.id/index.php/asset/article/download/2254/967) | OD matrix research from AFC | Public paper | Medium-high |
| LRT operation/capacity research | [link](https://dinastires.org/JAFM/article/download/3133/2184) | LRT capacity scenario | Public paper | Medium |
| KCI KMT integration | [link](https://kci.id/informasi-publik/berita/kembangkan-integrasi-sistem-pembayaran-kai-commuter-gandeng-bus-metro-jabar-trans-permudah-transaksi-pembayaran-tiket-dengan-kartu-multi-trip) | Payment integration context | Public info | Medium |
| QRIS Tap explainer | [link](https://www.cnnindonesia.com/edukasi/20251104100932-561-1291591/cara-pakai-qris-tap-naik-krl-transjakarta-mrt-dan-lrt) | QRIS Tap public flow | Public media | Medium |
| BPTJ Satu Matrix/data sharing | [link](https://www.bindo.id/news/info-nasional/transportasi/2023/10/bptj-bersama-damri-dishub-dki-jakarta-dan-kci-sepakati-tingkatkan-integrasi-data-dan-informasi/) | Institutional data sharing context | Public media | Medium |
| ANTARA Transjakarta 2024 | [link](https://www.antaranews.com/berita/4630905/pelanggan-transjakarta-capai-371-juta-pelanggan-di-2024) | Ridership/fleet confirmation | Public media quoting official | Medium-high |
| ANTARA Transjakarta 2023 | [link](https://www.antaranews.com/berita/4261231/produktivitas-operasional-dan-kepuasan-konsumen-transjakarta-meningkat) | 2023 productivity/fleet/ridership | Public media quoting official | Medium-high |
| ANTARA Commuter Line Nataru | [link](https://megapolitan.antaranews.com/berita/332118/ada-12-juta-pengguna-commuter-line-pada-akhir-tahun-2024) | Station/ridership spike context | Public media | Medium |
| Merdeka KRL 2024 | [link](https://www.merdeka.com/uang/ternyata-pengguna-krl-sepanjang-tahun-2024-mencapai-374-juta-orang-paling-banyak-di-jabodetabek-295565-mvk.html) | 2024 KCI ridership quote | Public media | Medium |
| Bisnis KRL 2025 projection | [link](https://ekonomi.bisnis.com/read/20250131/98/1835667/penumpang-krl-diprediksi-tembus-383-juta-orang-sepanjang-2025) | 2025 KCI projection | Public media | Medium |
| Kompas AI passenger camera | [link](https://megapolitan.kompas.com/read/2025/08/21/16405441/dishub-uji-coba-kamera-ai-hitung-jumlah-penumpang-transjabodetabek) | Passenger density camera trial | Public media | Medium |
| Media Indonesia CCTV Jakarta | [link](https://mediaindonesia.com/megapolitan/891389/27000-cctv-jakarta-akan-awasi-kota-real-time) | CCTV integration context | Public media | Medium |

## 14. Recommended Positioning For Proposal

Gunakan framing berikut:

1. **Prototype-ready today**: Transjakarta GTFS, BPS/public ridership, official reports, traffic recap, weather/flood APIs, and synthetic/anonymized tap sample.
2. **Production-grade with partners**: AFC tap-in/tap-out, AVL/GPS/GTFS-RT, actual schedule logs, fleet registry, occupancy, and incident logs from Dishub/JakLingko/operators.
3. **AI value**: bukan hanya prediksi ETA, tetapi closed-loop optimizer yang membaca demand, supply, disruption, dan transfer friction untuk memberi rekomendasi headway, dispatch, dan intermodal connection.
4. **Risk control**: privacy-by-design untuk AFC, uncertainty band untuk kapasitas armada, dan fallback public-data mode ketika real-time data belum tersedia.

## 15. Next Analytical Steps

1. Download dan parse `file_gtfs.zip` Transjakarta.
2. Build station/halte graph plus transfer nodes ke MRT/LRT/KRL.
3. Buat synthetic AFC table dari skema tap-in/tap-out untuk demo.
4. Buat fleet capacity assumption table per moda.
5. Tambahkan flood/weather layer dari PetaBencana dan BMKG MEWS.
6. Definisikan KPI: ETA error, headway adherence, load factor, passenger waiting time, transfer miss rate, and fleet utilization.
