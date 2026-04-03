"""
WebSocket Endpoint — AgriSmart AI Real-time Feed

URL koneksi dari frontend:
  ws://localhost:8000/ws

Format pesan yang diterima client (JSON):
  {
    "tipe": "sensor_update | pompa_update | rekomendasi_pupuk |
             rekomendasi_pestisida | alert | connected | reset_sesi",
    "data": { ... isi data sesuai tipe ... },
    "timestamp": "2025-01-15T08:30:00.000Z"
  }

Client juga bisa kirim pesan ke server (ping / request data):
  { "aksi": "ping" }
  { "aksi": "get_status" }
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from app.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket utama.

    Frontend connect ke ws://localhost:8001/ws
    Semua event real-time (sensor, pompa, rekomendasi, alert) dikirim ke sini.
    """
    await manager.connect(websocket)

    # Kirim snapshot data terkini saat client baru connect
    await _kirim_snapshot_awal(websocket)

    try:
        while True:
            # Tunggu pesan dari client (ping, request, dll)
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                pesan = json.loads(raw)
                await _proses_pesan_client(websocket, pesan)
            except asyncio.TimeoutError:
                # Kirim heartbeat setiap 60 detik agar koneksi tidak mati
                try:
                    await websocket.send_text(json.dumps({
                        "tipe":      "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "client_count": manager.jumlah_client,
                    }))
                except Exception:
                    break
            except json.JSONDecodeError:
                await _send_error(websocket, "Format pesan tidak valid, gunakan JSON")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def _kirim_snapshot_awal(websocket: WebSocket):
    """
    Kirim data terkini ke client yang baru saja connect
    agar dashboard langsung terisi tanpa menunggu event berikutnya.
    """
    from app.database import SessionLocal
    from app.services.sensor_service import baca_sensor_json, get_atau_buat_sesi, evaluasi_kondisi_tanah
    from app.services.pompa_service import get_status_pompa
    from app.services.db_service import ambil_riwayat_rekomendasi, ambil_statistik
    from app.services.pestisida_db_service import ambil_riwayat_pestisida

    db = SessionLocal()
    try:
        # Sensor
        try:
            raw     = baca_sensor_json()
            sensors = raw.get("sensors", {})
            status_tanah = evaluasi_kondisi_tanah(
                ph=sensors.get("ph_tanah", 7.0),
                n =sensors.get("nitrogen", 0),
                p =sensors.get("fosfor", 0),
                k =sensors.get("kalium", 0),
            )
            sensor_payload = {**sensors, **status_tanah,
                              "device_id": raw.get("device_id"),
                              "lokasi":    raw.get("lokasi")}
        except Exception:
            sensor_payload = {}

        snapshot = {
            "tipe":      "snapshot",
            "data": {
                "sesi_aktif":        get_atau_buat_sesi(),
                "sensor":            sensor_payload,
                "pompa":             get_status_pompa(db),
                "statistik":         ambil_statistik(db),
                "riwayat_pupuk":     ambil_riwayat_rekomendasi(db, limit=5),
                "riwayat_pestisida": ambil_riwayat_pestisida(db, limit=5),
            },
            "timestamp": datetime.now().isoformat(),
        }

        await websocket.send_text(json.dumps(snapshot, ensure_ascii=False, default=str))

    except Exception as e:
        await _send_error(websocket, f"Gagal memuat snapshot: {e}")
    finally:
        db.close()


async def _proses_pesan_client(websocket: WebSocket, pesan: dict):
    """
    Proses pesan yang dikirim client ke server.

    Aksi yang didukung:
    - ping        → balas pong
    - get_status  → kirim snapshot data terkini
    - get_pompa   → kirim status pompa saja
    """
    aksi = pesan.get("aksi", "")

    if aksi == "ping":
        await websocket.send_text(json.dumps({
            "tipe":      "pong",
            "timestamp": datetime.now().isoformat(),
        }))

    elif aksi == "get_status":
        await _kirim_snapshot_awal(websocket)

    elif aksi == "get_pompa":
        from app.database import SessionLocal
        from app.services.pompa_service import get_status_pompa
        db = SessionLocal()
        try:
            status = get_status_pompa(db)
            await websocket.send_text(json.dumps({
                "tipe":      "pompa_update",
                "data":      status,
                "timestamp": datetime.now().isoformat(),
            }, default=str))
        finally:
            db.close()

    else:
        await _send_error(websocket, f"Aksi '{aksi}' tidak dikenal")


async def _send_error(websocket: WebSocket, pesan: str):
    try:
        await websocket.send_text(json.dumps({
            "tipe":      "error",
            "pesan":     pesan,
            "timestamp": datetime.now().isoformat(),
        }))
    except Exception:
        pass


# ── Info endpoint (HTTP) ──────────────────────────────────────────────────────

ws_info_router = APIRouter(tags=["WebSocket"])

@ws_info_router.get("/ws/info", summary="Info koneksi WebSocket")
def get_ws_info():
    """Info jumlah client yang sedang terhubung dan cara penggunaan WebSocket."""
    return {
        "url_koneksi":    "ws://localhost:8001/ws",
        "jumlah_client":  manager.jumlah_client,
        "tipe_event": [
            "connected",
            "snapshot",
            "sensor_update",
            "pompa_update",
            "rekomendasi_pupuk",
            "rekomendasi_pestisida",
            "saran_tanaman",
            "alert",
            "heartbeat",
            "error",
        ],
        "aksi_dari_client": ["ping", "get_status", "get_pompa"],
        "contoh_javascript": (
            "const ws = new WebSocket('ws://localhost:8000/ws');\n"
            "ws.onmessage = (e) => {\n"
            "  const msg = JSON.parse(e.data);\n"
            "  if (msg.tipe === 'sensor_update') updateSensor(msg.data);\n"
            "  if (msg.tipe === 'pompa_update')  updatePompa(msg.data);\n"
            "  if (msg.tipe === 'alert')         tampilAlert(msg.data);\n"
            "};"
        ),
    }