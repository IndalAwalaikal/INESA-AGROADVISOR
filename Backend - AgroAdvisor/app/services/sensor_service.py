import uuid
from datetime import datetime
from pathlib import Path
import json

SENSOR_FILE = Path(__file__).parent.parent.parent / "data" / "sensor_data.json"

# State sesi aktif (in-memory; diganti Redis saat IoT tersambung)
_sesi_aktif: dict = {
    "sesi_id":    None,
    "dibuat_pada": None,
}


# State sensor terkini dari IoT (in-memory)
_sensor_terkini: dict = {
    "device_id": None,
    "timestamp": None,
    "lokasi":    "Lahan Utama",
    "sensors":   {},
}

# ─── File JSON & Data Terkini ────────────────────────────────────────────────

def update_sensor_iot(data: dict):
    """Update data sensor dari perangkat IoT asli."""
    _sensor_terkini["device_id"] = data.get("device_id", "esp32_iot")
    _sensor_terkini["timestamp"] = datetime.now().isoformat()
    _sensor_terkini["sensors"]   = {
        "suhu_udara":       data.get("suhu_udara"),
        "kelembaban_udara": data.get("kelembaban_udara"),
        "ph_tanah":         data.get("ph_tanah"),
        "nitrogen":        data.get("nitrogen"),
        "fosfor":          data.get("fosfor"),
        "kalium":          data.get("kalium"),
        "kelembaban_tanah": data.get("kelembaban_tanah"),
        "hujan_terdeteksi": data.get("hujan_terdeteksi"),
    }

def baca_sensor_json() -> dict:
    """
    Ambil data sensor. 
    Prioritas: Data IoT asli (jika ada), fallback ke file JSON (untuk demo).
    """
    if _sensor_terkini["sensors"]:
        return _sensor_terkini

    if not SENSOR_FILE.exists():
        raise FileNotFoundError(f"File sensor tidak ditemukan: {SENSOR_FILE}")
    with open(SENSOR_FILE, "r") as f:
        return json.load(f)


# ─── Manajemen Sesi ───────────────────────────────────────────────────────────

def _buat_sesi_id() -> str:
    return f"SESI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"


def get_atau_buat_sesi() -> str:
    """Kembalikan sesi aktif; buat baru jika belum ada."""
    if _sesi_aktif["sesi_id"] is None:
        _sesi_aktif["sesi_id"]    = _buat_sesi_id()
        _sesi_aktif["dibuat_pada"] = datetime.now().isoformat()
    return _sesi_aktif["sesi_id"]


def reset_sesi() -> str:
    """
    Buat sesi baru. Data sesi lama TETAP tersimpan di database
    dan akan digunakan AI sebagai konteks pembelajaran.
    """
    _sesi_aktif["sesi_id"]    = _buat_sesi_id()
    _sesi_aktif["dibuat_pada"] = datetime.now().isoformat()
    return _sesi_aktif["sesi_id"]


def get_info_sesi() -> dict:
    return {
        "sesi_id":    get_atau_buat_sesi(),
        "dibuat_pada": _sesi_aktif["dibuat_pada"],
    }


# ─── Evaluasi Kondisi Tanah ───────────────────────────────────────────────────

def evaluasi_kondisi_tanah(ph: float, n: float, p: float, k: float) -> dict:
    """
    Evaluasi status tiap parameter tanah.
    Kembalikan label: sangat_rendah | rendah | normal | tinggi | dll.
    """
    def status_ph(v):
        if v < 5.5:  return "sangat_asam"
        if v < 6.0:  return "asam"
        if v <= 7.0: return "normal"
        if v <= 7.5: return "basa_ringan"
        return "basa"

    def status_n(v):
        if v < 30:   return "sangat_rendah"
        if v < 50:   return "rendah"
        if v <= 100: return "normal"
        return "tinggi"

    def status_p(v):
        if v < 10:  return "sangat_rendah"
        if v < 20:  return "rendah"
        if v <= 40: return "normal"
        return "tinggi"

    def status_k(v):
        if v < 60:   return "sangat_rendah"
        if v < 100:  return "rendah"
        if v <= 200: return "normal"
        return "tinggi"

    return {
        "status_ph":       status_ph(ph),
        "status_nitrogen": status_n(n),
        "status_fosfor":   status_p(p),
        "status_kalium":   status_k(k),
    }