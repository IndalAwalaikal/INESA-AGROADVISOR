# 🌱 AgriSmart AI — Backend

Sistem rekomendasi pertanian cerdas berbasis AI untuk pertanian presisi.
**Stack:** Python · FastAPI · Claude/Gemini AI · MySQL (XAMPP) · WebSocket · FPDF2

---

## Fitur Utama

- **Pupuk AI** — Rekomendasi pupuk spesifik per tanaman berdasarkan pH & NPK tanah aktual.
- **Pestisida AI** — Identifikasi hama & penyakit serta rekomendasi dosis, jadwal semprot, dan PHI.
- **Irigasi Otomatis (Pompa)** — Rule-engine & kontrol manual/otomatis berdasarkan suhu dan kelembaban.
- **Real-time Monitoring** — Push update data sensor ke dashboard menggunakan WebSockets.
- **Download PDF** — Cetak hasil rekomendasi AI secara instan dalam format PDF profesional.

---

## Struktur Project

```
agrismart/
├── main.py                          # Entry point FastAPI & WebSocket manager
├── .env                             # Konfigurasi API Key & Database
├── requirements.txt
├── data/
│   └── sensor_data.json             # ← Simulasi Data IoT (edit untuk pengujian)
└── app/
    ├── database.py                  # Koneksi MySQL + Schema Tabel
    ├── routes/
    │   ├── pupuk.py                 # API Rekomendasi Pupuk & PDF
    │   ├── pestisida.py             # API Rekomendasi Pestisida & PDF
    │   ├── pompa.py                 # API Kontrol Irigasi
    │   └── ws.py                    # Real-time WebSocket handlers
    └── services/
        ├── ai_service.py            # Claude AI: Analisis Pupuk
        ├── pestisida_ai_service.py   # Claude AI: Analisis Hama
        ├── pdf_service.py           # Engine PDF (FPDF2)
        ├── db_service.py            # Operasi Data Pupuk & Lahan
        ├── pestisida_db_service.py  # Operasi Data Pestisida
        └── sensor_service.py        # Logic Sensor & Manajemen Sesi
```

---

## Setup & Menjalankan

### 1. Prasyarat

- Python 3.10+
- XAMPP (MySQL aktif)
- API Key (Gemini/Anthropic)

### 2. Install dependencies

```bash
# Gunakan virtual environment (opsional tapi disarankan)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Konfigurasi .env

```bash
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=agrismart
DB_USER=root
DB_PASSWORD=your_password
APP_PORT=8001
GEMINI_API_KEY=your_key_here
```

### 4. Jalankan server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

## Endpoint API Utama

| Method | URL                                   | Fungsi                            |
| ------ | ------------------------------------- | --------------------------------- |
| POST   | `/api/pupuk/rekomendasi`              | AI: Generate rekomendasi pupuk    |
| POST   | `/api/pestisida/rekomendasi`          | AI: Identifikasi hama & solusi    |
| GET    | `/api/pupuk/rekomendasi/{id}/pdf`     | Download laporan PDF Pupuk        |
| GET    | `/api/pestisida/rekomendasi/{id}/pdf` | Download laporan PDF Pestisida    |
| POST   | `/api/pompa/manual`                   | Kontrol pompa manual (On/Off)     |
| PUT    | `/api/pompa/konfigurasi`              | Update threshold irigasi otomatis |
| GET    | `/dashboard`                          | Agregat data untuk dashboard awal |
| WS     | `/ws`                                 | Real-time push sensor & event     |

---

## Download PDF

Sistem mendukung pembuatan laporan PDF otomatis yang mencakup:

1.  **Analisis Kondisi**: pH, Nitrogen, Fosfor, Kalium aktual.
2.  **Detail Produk**: Nama pupuk/pestisida, dosis per HA/liter, dan cara aplikasi.
3.  **Jadwal & Keamanan**: Kapan pengaplikasian dilakukan dan peringatan keselamatan.

---

## Roadmap Terupdate

- [x] Modul rekomendasi pupuk (AI)
- [x] Modul rekomendasi pestisida (AI)
- [x] Kontrol pompa otomatis & manual
- [x] WebSocket real-time updates
- [x] Fitur cetak/export PDF
- [ ] Integrasi hardware ESP32 (MQTT)
- [ ] Analisis citra daun (Image Processing)

.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload