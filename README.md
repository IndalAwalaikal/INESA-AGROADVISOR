# AgroAdvisor

**Sistem Rekomendasi Pertanian Cerdas Berbasis IoT & AI**

Platform web full-stack untuk pertanian presisi — mencakup **rekomendasi pupuk & pestisida berbasis AI**, **kontrol irigasi otomatis**, **monitoring sensor real-time via WebSocket**, dan **prakiraan cuaca**.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.2-06B6D4?logo=tailwindcss&logoColor=white)

---

## Daftar Isi

- [Arsitektur](#arsitektur)
- [Tech Stack](#tech-stack)
- [Struktur Project](#struktur-project)
- [Prasyarat](#prasyarat)
- [Quick Start — Docker](#quick-start--docker)
- [Quick Start — Development](#quick-start--development)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Fitur](#fitur)
- [Docker Services](#docker-services)
- [Perintah Berguna](#perintah-berguna)

---

## Arsitektur

```
                    ┌─────────────────────────────────────────┐
                    │              Internet / LAN              │
                    └────────────────┬────────────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                    │
            :3000│             :8001│               :3306│
                 ▼                  ▼                    ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │    Frontend       │  │    Backend        │  │    Database       │
   │  Next.js 16 (SSR) │  │  FastAPI+Uvicorn  │  │    MySQL 8.0     │
   │  Tailwind CSS v4  │──│  Gemini / Groq AI │──│   agroadvisor    │
   │  shadcn/ui        │  │  WebSocket        │  │                  │
   └──────────────────┘  └────────┬───────────┘  └──────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────────┐
              │ Sensor   │ │ OpenWeather│ │ Gemini/Groq │
              │ IoT/JSON │ │ API       │ │ AI API      │
              └──────────┘ └──────────┘ └──────────────┘

              ─────── agroadvisor-network (Docker) ───────
```

---

## Tech Stack

| Layer | Teknologi |
|-------|-----------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, Recharts, Axios |
| **Backend** | Python 3.11, FastAPI, Uvicorn, SQLAlchemy, PyMySQL |
| **AI Engine** | Google Gemini API, Groq API |
| **Database** | MySQL 8.0 |
| **Real-time** | WebSocket (native FastAPI) |
| **Cuaca** | OpenWeatherMap API |
| **Containerization** | Docker, Docker Compose |

---

## Struktur Project

```
AgroAdvisor/
├── docker-compose.yml              # Orkestrasi semua service
├── README.md                       # Dokumentasi ini
│
├── Backend - AgroAdvisor/          # FastAPI REST API + WebSocket
│   ├── Dockerfile                  # Build image backend
│   ├── .dockerignore
│   ├── .env.example                # Template environment variables
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # Entry point (FastAPI app)
│   ├── app/
│   │   ├── database.py             # Koneksi DB & auto-create tabel
│   │   ├── websocket_manager.py    # WebSocket connection manager
│   │   ├── scheduler.py            # Background jobs (APScheduler)
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── pupuk.py            # Endpoint rekomendasi pupuk
│   │   │   ├── pestisida.py        # Endpoint rekomendasi pestisida
│   │   │   ├── pompa.py            # Endpoint kontrol pompa irigasi
│   │   │   ├── cuaca.py            # Endpoint prakiraan cuaca
│   │   │   ├── iot.py              # Endpoint penerimaan data sensor
│   │   │   ├── auth.py             # Endpoint login admin
│   │   │   └── ws.py               # WebSocket endpoint
│   │   ├── services/
│   │   │   ├── ai_service.py       # Integrasi Gemini/Groq (pupuk)
│   │   │   ├── pestisida_ai_service.py  # AI rekomendasi pestisida
│   │   │   ├── pompa_service.py    # Logika kontrol pompa otomatis
│   │   │   ├── sensor_service.py   # Baca data sensor JSON/IoT
│   │   │   ├── weather_service.py  # OpenWeatherMap integration
│   │   │   ├── rule_engine.py      # Rule-based evaluasi tanah
│   │   │   ├── db_service.py       # CRUD database pupuk
│   │   │   ├── pestisida_db_service.py  # CRUD database pestisida
│   │   │   ├── pdf_service.py      # Generate PDF rekomendasi
│   │   │   ├── export_service.py   # Export CSV riwayat
│   │   │   ├── jadwal_service.py   # Manajemen jadwal pompa
│   │   │   └── cleanup_service.py  # Auto-cleanup data lama
│   │   └── scripts/
│   │       └── seed_pests.py       # Seed master data hama
│   ├── data/
│   │   └── sensor_data.json        # Data sensor statis (dev)
│   └── schema/
│       └── 001_agroadvisor.sql     # SQL schema referensi
│
└── Frontend - AgroAdvisor/         # Next.js Dashboard
    ├── Dockerfile                  # Multi-stage build (builder + prod)
    ├── .dockerignore
    ├── package.json                # Node dependencies
    ├── next.config.mjs             # Next.js configuration
    ├── postcss.config.mjs          # PostCSS + Tailwind CSS v4
    ├── tsconfig.json               # TypeScript config + path aliases
    ├── middleware.ts               # Auth guard (/dashboard → /login)
    ├── app/
    │   ├── layout.tsx              # Root layout
    │   ├── page.tsx                # Landing page
    │   ├── globals.css             # Global styles (Tailwind)
    │   ├── login/                  # Halaman login admin
    │   ├── dashboard/
    │   │   ├── page.tsx            # Dashboard utama (overview)
    │   │   ├── layout.tsx          # Sidebar navigation
    │   │   ├── pupuk/              # Halaman rekomendasi pupuk
    │   │   ├── pestisida/          # Halaman rekomendasi pestisida
    │   │   ├── pompa/              # Halaman kontrol pompa irigasi
    │   │   └── riwayat/            # Halaman riwayat & export
    │   ├── context/
    │   │   └── WebSocketContext.tsx # Provider WebSocket real-time
    │   └── utils/
    │       └── api.ts              # Axios API client
    ├── components/                 # shadcn/ui components
    ├── hooks/                      # Custom React hooks
    ├── lib/                        # Utility functions
    ├── styles/                     # Additional styles
    └── public/                     # Static assets (favicon, images)
```

---

## Prasyarat

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Git](https://git-scm.com/)
- (Development opsional) Python 3.11+, Node.js 20+

---

## Quick Start — Docker

```bash
# 1. Clone repository
git clone <repository-url>
cd AgroAdvisor

# 2. Siapkan file environment backend
cp "Backend - AgroAdvisor/.env.example" "Backend - AgroAdvisor/.env"

# 3. Edit .env sesuai kebutuhan
nano "Backend - AgroAdvisor/.env"
# → Isi GEMINI_API_KEY, DB_PASSWORD, OPENWEATHER_API_KEY, dll

# 4. Jalankan semua service
docker compose up --build

# 5. Akses
# Frontend  : http://localhost:3000
# Backend   : http://localhost:8001
# API Docs  : http://localhost:8001/docs
# WebSocket : ws://localhost:8001/ws
```

---

## Quick Start — Development

### Backend

```bash
cd "Backend - AgroAdvisor"

# Buat virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Siapkan .env
cp .env.example .env
nano .env

# Pastikan MySQL berjalan (XAMPP / Docker)
# Jalankan server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd "Frontend - AgroAdvisor"

# Install dependencies
npm install

# Jalankan dev server
npm run dev

# Akses: http://localhost:3000
```

---

## Environment Variables

### Backend (`Backend - AgroAdvisor/.env`)

| Variable | Contoh | Keterangan |
|----------|--------|------------|
| `GEMINI_API_KEY` | `AIzaSy...` | API key Google Gemini AI |
| `GROQ_API_KEY` | `gsk_...` | API key Groq (AI fallback) |
| `DB_HOST` | `db` | Hostname database (`db` di Docker, `localhost` di dev) |
| `DB_PORT` | `3306` | Port MySQL |
| `DB_NAME` | `agroadvisor` | Nama database |
| `DB_USER` | `root` | User database |
| `DB_PASSWORD` | `password123` | Password database |
| `APP_HOST` | `0.0.0.0` | Host binding server |
| `APP_PORT` | `8001` | Port server API |
| `ADMIN_USERNAME` | `admin` | Username login dashboard |
| `ADMIN_PASSWORD` | `admin123` | Password login dashboard |
| `ADMIN_TOKEN` | `secret_token` | Token autentikasi admin |
| `OPENWEATHER_API_KEY` | `1acbb4f...` | API key OpenWeatherMap |
| `OPENWEATHER_LAT` | `-6.2` | Latitude lokasi pertanian |
| `OPENWEATHER_LON` | `106.8` | Longitude lokasi pertanian |

---

## API Endpoints

### Info & Health

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `GET` | `/` | Info aplikasi & daftar endpoint |
| `GET` | `/health` | Health check |
| `GET` | `/dashboard` | Agregat semua data dashboard |
| `GET` | `/docs` | Swagger UI (auto-generated) |

### Pupuk (AI Recommendation)

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `GET` | `/api/pupuk/sensor/status` | Status sensor tanah |
| `GET` | `/api/pupuk/saran-tanaman` | Saran tanaman berdasarkan kondisi tanah |
| `GET` | `/api/pupuk/tanaman/daftar` | Daftar tanaman tersedia |
| `POST` | `/api/pupuk/rekomendasi` | Generate rekomendasi pupuk (AI) |
| `POST` | `/api/pupuk/alur2-saran` | Alur saran pupuk alternatif |
| `POST` | `/api/pupuk/feedback` | Feedback rekomendasi |
| `POST` | `/api/pupuk/reset-sesi` | Reset sesi pengujian |
| `GET` | `/api/pupuk/riwayat` | Riwayat rekomendasi pupuk |
| `GET` | `/api/pupuk/statistik` | Statistik penggunaan |
| `GET` | `/api/pupuk/rekomendasi/:id/pdf` | Download PDF rekomendasi |
| `GET` | `/api/pupuk/riwayat/export/csv` | Export riwayat ke CSV |

### Pestisida (AI Recommendation)

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `POST` | `/api/pestisida/rekomendasi` | Generate rekomendasi pestisida (AI) |
| `GET` | `/api/pestisida/hama/daftar` | Daftar hama per tanaman |
| `GET` | `/api/pestisida/riwayat` | Riwayat rekomendasi pestisida |
| `POST` | `/api/pestisida/feedback` | Feedback rekomendasi |
| `GET` | `/api/pestisida/rekomendasi/:id/pdf` | Download PDF rekomendasi |
| `GET` | `/api/pestisida/riwayat/export/csv` | Export riwayat ke CSV |

### Pompa Irigasi

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `GET` | `/api/pompa/status` | Status pompa saat ini |
| `POST` | `/api/pompa/manual` | Kontrol manual (nyala/mati) |
| `POST` | `/api/pompa/otomatis` | Aktifkan mode otomatis |
| `GET` | `/api/pompa/konfigurasi` | Lihat konfigurasi pompa |
| `PUT` | `/api/pompa/konfigurasi` | Update konfigurasi pompa |
| `GET` | `/api/pompa/riwayat` | Riwayat aktivitas pompa |
| `GET` | `/api/pompa/jadwal` | Daftar jadwal pompa |
| `POST` | `/api/pompa/jadwal` | Tambah jadwal pompa |
| `DELETE` | `/api/pompa/jadwal/:id` | Hapus jadwal |
| `PUT` | `/api/pompa/jadwal/:id/toggle` | Toggle aktif/nonaktif jadwal |
| `GET` | `/api/pompa/riwayat/export/csv` | Export riwayat ke CSV |

### Cuaca

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `GET` | `/api/cuaca/sekarang` | Cuaca saat ini |
| `GET` | `/api/cuaca/prakiraan` | Prakiraan cuaca |
| `GET` | `/api/cuaca/hujan-alert` | Peringatan hujan |

### IoT & WebSocket

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `POST` | `/api/iot/sensor` | Kirim data sensor dari perangkat IoT |
| `WS` | `/ws` | WebSocket real-time events |
| `GET` | `/ws/info` | Info koneksi WebSocket aktif |

### Auth

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `POST` | `/api/auth/login` | Login admin dashboard |

---

## Fitur

### 🌱 Rekomendasi Pupuk (AI)
- Analisis kondisi tanah dari sensor (pH, N, P, K)
- Rekomendasi pupuk spesifik per tanaman oleh AI (Gemini/Groq)
- Detail takaran, waktu, dan metode aplikasi
- Download PDF & export CSV riwayat
- Feedback rating untuk perbaikan rekomendasi

### 🐛 Rekomendasi Pestisida (AI)
- Identifikasi hama berdasarkan master data
- Rekomendasi pestisida berbasis PHT (Pengelolaan Hama Terpadu)
- Informasi PHI (Pre-Harvest Interval)
- Download PDF & export CSV

### 💧 Kontrol Pompa Irigasi
- Mode otomatis berdasarkan suhu & kelembaban
- Kontrol manual on/off via dashboard
- Jadwal penyiraman terjadwal (cron)
- Konfigurasi threshold suhu & kelembaban
- Riwayat lengkap aktivitas pompa

### 🌤️ Prakiraan Cuaca
- Data cuaca real-time (OpenWeatherMap API)
- Prakiraan cuaca mendatang
- Peringatan hujan otomatis

### 📡 Real-time Monitoring
- WebSocket push semua event ke dashboard
- Update sensor, pompa, cuaca secara real-time
- Tanpa polling — efisien & instan

### 🔐 Admin Dashboard
- Login dengan autentikasi token
- Middleware proteksi route `/dashboard`
- Overview statistik lengkap

---

## Docker Services

| Service | Container | Port | Image | Keterangan |
|---------|-----------|------|-------|------------|
| `db` | agroadvisor-db | `3306` | `mysql:8.0` | Database MySQL + volume persistent |
| `backend` | agroadvisor-backend | `8001` | Build dari Dockerfile | FastAPI + Uvicorn, auto-create tabel |
| `frontend` | agroadvisor-frontend | `3000` | Build dari Dockerfile | Next.js 16 multi-stage build |

---

## Perintah Berguna

```bash
# Jalankan semua service (background)
docker compose up -d --build

# Lihat log
docker compose logs -f
docker compose logs -f backend     # log backend saja

# Restart satu service
docker compose restart backend

# Stop semua
docker compose down

# Stop & hapus volume (reset database)
docker compose down -v

# Masuk ke container MySQL
docker exec -it agroadvisor-db mysql -uroot -p agroadvisor

# Cek health
curl http://localhost:8001/health
```

---

## Database Schema

Database `agroadvisor` terdiri dari **10 tabel** yang otomatis dibuat saat backend startup:

| Tabel | Keterangan |
|-------|------------|
| `sesi_pengujian` | Sesi pengujian tanah aktif |
| `log_sensor` | Log data sensor IoT |
| `rekomendasi_pupuk` | Hasil rekomendasi AI pupuk |
| `detail_pupuk` | Detail item per rekomendasi pupuk |
| `rekomendasi_pestisida` | Hasil rekomendasi AI pestisida |
| `detail_pestisida` | Detail item per rekomendasi pestisida |
| `feedback_rekomendasi` | Rating & feedback pengguna |
| `log_pompa` | Riwayat aktivitas pompa |
| `konfigurasi_pompa` | Setting threshold pompa (1 row) |
| `jadwal_pompa` | Jadwal penyiraman terjadwal |
| `kebutuhan_hara` | Master data kebutuhan hara tanaman |
| `master_hama_penyakit` | Master data hama & penyakit |

> **Catatan:** Tabel dibuat otomatis oleh `init_db()` di `app/database.py`. File `schema/001_agroadvisor.sql` adalah referensi saja.

---

## Lisensi

AgroAdvisor Project
