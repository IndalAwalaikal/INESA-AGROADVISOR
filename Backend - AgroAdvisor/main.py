from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import init_db
from app.routes.pupuk     import router as pupuk_router
from app.routes.pestisida import router as pestisida_router
from app.routes.pompa     import router as pompa_router
from app.routes.cuaca     import router as cuaca_router
from app.routes.ws        import router as ws_router, ws_info_router
from app.routes.auth      import router as auth_router
from app.routes.iot       import router as iot_router
from app.scheduler        import start_scheduler, stop_scheduler

load_dotenv()

app = FastAPI(
    title    = "AgriSmart AI — Backend",
    description = """
## Sistem Rekomendasi Pertanian Cerdas

Backend API untuk pertanian presisi berbasis sensor IoT dan AI (Claude — Anthropic).

### Modul
- **Pupuk** — Rekomendasi pupuk spesifik per tanaman berdasarkan pH & NPK tanah aktual
- **Pestisida** — Rekomendasi pengendalian hama berbasis PHT dengan PHI
- **Pompa** — Kontrol irigasi otomatis berbasis sensor suhu & kelembaban
- **WebSocket** — Real-time push semua event ke dashboard tanpa polling

### Catatan
- Dashboard **publik** — tidak perlu login
- AI menggunakan **Claude (Anthropic)** via API
- Data sensor saat ini dari **file JSON statis** (akan diganti MQTT IoT)
    """,
    version  = "1.0.0",
    docs_url = "/docs",
    redoc_url= "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["*"],
    allow_credentials= True,
    allow_methods    = ["*"],
    allow_headers    = ["*"],
)

# Daftarkan semua router
app.include_router(pupuk_router)
app.include_router(pestisida_router)
app.include_router(pompa_router)
app.include_router(cuaca_router)
app.include_router(ws_router)
app.include_router(ws_info_router)
app.include_router(auth_router)
app.include_router(iot_router)


@app.on_event("startup")
def on_startup():
    print("AgriSmart AI Backend starting...")
    try:
        init_db()
    except Exception as e:
        print(f"Gagal koneksi database: {e}")
        print("Pastikan XAMPP MySQL berjalan dan database 'agrismart' sudah dibuat.")
        return

    # Mulai background scheduler
    start_scheduler()
    print("Server siap di http://localhost:8001")
    print("Dokumentasi API  : http://localhost:8001/docs")
    print("WebSocket URL    : ws://localhost:8001/ws")
    print("Dashboard data   : http://localhost:8001/dashboard")


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()
    print("AgriSmart AI Backend stopped.")


@app.get("/", tags=["Info"])
def root():
    return {
        "status": "online",
        "app":    "AgriSmart AI Backend v1.0.0",
        "docs":   "/docs",
        "websocket": "ws://localhost:8001/ws",
        "modul": {
            "pupuk": {
                "sensor_status":  "GET  /api/pupuk/sensor/status",
                "saran_tanaman":  "GET  /api/pupuk/saran-tanaman",
                "daftar_tanaman": "GET  /api/pupuk/tanaman/daftar",
                "rekomendasi":    "POST /api/pupuk/rekomendasi",
                "feedback":       "POST /api/pupuk/feedback",
                "reset_sesi":     "POST /api/pupuk/reset-sesi",
                "riwayat":        "GET  /api/pupuk/riwayat",
                "statistik":      "GET  /api/pupuk/statistik",
            },
            "pestisida": {
                "rekomendasi": "POST /api/pestisida/rekomendasi",
                "daftar_hama": "GET  /api/pestisida/hama/daftar",
                "riwayat":     "GET  /api/pestisida/riwayat",
            },
            "pompa": {
                "status":        "GET  /api/pompa/status",
                "manual":        "POST /api/pompa/manual",
                "otomatis":      "POST /api/pompa/otomatis",
                "konfigurasi":   "GET  /api/pompa/konfigurasi",
                "update_config": "PUT  /api/pompa/konfigurasi",
                "riwayat":       "GET  /api/pompa/riwayat",
            },
            "websocket": {
                "koneksi": "WS   /ws",
                "info":    "GET  /ws/info",
            },
            "cuaca": {
                "sekarang":    "GET  /api/cuaca/sekarang",
                "prakiraan":   "GET  /api/cuaca/prakiraan",
                "hujan_alert": "GET  /api/cuaca/hujan-alert",
            },
        },
    }


@app.get("/dashboard", tags=["Info"])
async def dashboard_data():
    """
    Endpoint agregat — semua data dashboard dalam satu request.
    Cocok untuk loading awal sebelum WebSocket terhubung.
    """
    from app.database import SessionLocal
    from app.services.sensor_service import baca_sensor_json, get_atau_buat_sesi, evaluasi_kondisi_tanah
    from app.services.pompa_service import get_status_pompa
    from app.services.db_service import ambil_statistik, ambil_riwayat_rekomendasi
    from app.services.pestisida_db_service import ambil_riwayat_pestisida
    from app.websocket_manager import manager
    import datetime

    db = SessionLocal()
    try:
        try:
            raw     = baca_sensor_json()
            sensors = raw.get("sensors", {})
            status_tanah = evaluasi_kondisi_tanah(
                ph=sensors.get("ph_tanah", 7),
                n =sensors.get("nitrogen", 0),
                p =sensors.get("fosfor", 0),
                k =sensors.get("kalium", 0),
            )
            sensor_data = {**sensors, **status_tanah,
                           "device_id": raw.get("device_id"),
                           "lokasi":    raw.get("lokasi"),
                           "timestamp": raw.get("timestamp")}
        except Exception:
            sensor_data = {}

        return {
            "sukses":             True,
            "sesi_aktif":         get_atau_buat_sesi(),
            "sensor":             sensor_data,
            "pompa":              get_status_pompa(db),
            "statistik":          ambil_statistik(db),
            "riwayat_pupuk":      ambil_riwayat_rekomendasi(db, limit=5),
            "riwayat_pestisida":  ambil_riwayat_pestisida(db, limit=5),
            "ws_client_aktif":    manager.jumlah_client,
            "diperbarui_pada":    datetime.datetime.now().isoformat(),
        }
    finally:
        db.close()


@app.get("/health", tags=["Info"])
def health():
    import datetime
    from app.websocket_manager import manager
    return {
        "status":          "ok",
        "ws_client_aktif": manager.jumlah_client,
        "timestamp":       datetime.datetime.now().isoformat(),
    }