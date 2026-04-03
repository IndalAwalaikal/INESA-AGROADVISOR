"""
Weather Service — Integrasi Prakiraan Cuaca OpenWeatherMap

Fitur:
- Fetch prakiraan cuaca 5 hari / 3 jam dari OpenWeatherMap API
- Cek apakah hujan diprediksi dalam N jam ke depan
- Cache in-memory dengan TTL 15 menit agar tidak spam API
- Jika API key tidak tersedia, return data dummy/fallback

Catatan:
- Gunakan API Key gratis dari https://openweathermap.org/api
- Tambahkan ke .env: OPENWEATHER_API_KEY, OPENWEATHER_LAT, OPENWEATHER_LON
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

from typing import Dict, Any

# ── Cache in-memory ──────────────────────────────────────────────────────────
_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": None,
    "ttl_menit": 15,
}

# Kode cuaca OpenWeatherMap yang termasuk hujan/badai
_KODE_HUJAN = {
    200, 201, 202, 210, 211, 212, 221, 230, 231, 232,  # Thunderstorm
    300, 301, 302, 310, 311, 312, 313, 314, 321,        # Drizzle
    500, 501, 502, 503, 504, 511, 520, 521, 522, 531,   # Rain
}

# Mapping kondisi cuaca ke Bahasa Indonesia
_KONDISI_MAP = {
    "Clear": "Cerah",
    "Clouds": "Berawan",
    "Rain": "Hujan",
    "Drizzle": "Gerimis",
    "Thunderstorm": "Badai Petir",
    "Snow": "Salju",
    "Mist": "Berkabut",
    "Fog": "Kabut",
    "Haze": "Kabur",
}


def _get_config():
    """Ambil konfigurasi cuaca dari environment."""
    return {
        "api_key": os.getenv("OPENWEATHER_API_KEY", ""),
        "lat": float(os.getenv("OPENWEATHER_LAT", "-6.2")),
        "lon": float(os.getenv("OPENWEATHER_LON", "106.8")),
    }


def _is_cache_valid() -> bool:
    """Cek apakah cache masih valid."""
    if _cache["data"] is None or _cache["timestamp"] is None:
        return False
    elapsed = (datetime.now() - _cache["timestamp"]).total_seconds() / 60
    return elapsed < _cache["ttl_menit"]


async def fetch_prakiraan_cuaca() -> dict | None:
    """
    Fetch prakiraan cuaca dari OpenWeatherMap API.
    Return None jika API key tidak tersedia atau request gagal.
    Cache selama 15 menit.
    """
    if _is_cache_valid():
        return _cache["data"]

    cfg = _get_config()
    if not cfg["api_key"]:
        logger.warning("OPENWEATHER_API_KEY tidak diset, cuaca dinonaktifkan")
        return None

    try:
        import httpx
        url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={cfg['lat']}&lon={cfg['lon']}"
            f"&appid={cfg['api_key']}"
            f"&units=metric&lang=id&cnt=16"  # 16 interval = 48 jam
        )
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        # Parse dan simpan ke cache
        parsed = _parse_response(data)
        _cache["data"] = parsed
        _cache["timestamp"] = datetime.now()
        return parsed

    except Exception as e:
        logger.error(f"Gagal fetch prakiraan cuaca: {e}")
        return _cache.get("data")  # Return last cache jika ada


def _parse_response(data: dict) -> dict:
    """Parse respons OpenWeatherMap menjadi format yang lebih mudah dibaca."""
    city = data.get("city", {})
    forecasts = []

    for item in data.get("list", []):
        dt = datetime.fromtimestamp(item["dt"])
        weather = item.get("weather", [{}])[0]
        main = item.get("main", {})
        rain = item.get("rain", {})

        kondisi_en = weather.get("main", "Unknown")
        kondisi_id = _KONDISI_MAP.get(kondisi_en, kondisi_en)

        forecasts.append({
            "waktu": dt.isoformat(),
            "waktu_str": dt.strftime("%d/%m %H:%M"),
            "suhu": round(main.get("temp", 0), 1),
            "kelembaban": main.get("humidity", 0),
            "kondisi": kondisi_id,
            "kondisi_en": kondisi_en,
            "kode_cuaca": weather.get("id", 0),
            "ikon": weather.get("icon", ""),
            "deskripsi": weather.get("description", ""),
            "curah_hujan_3jam": rain.get("3h", 0),
            "angin_kecepatan": item.get("wind", {}).get("speed", 0),
            "adalah_hujan": weather.get("id", 0) in _KODE_HUJAN,
        })

    # Cuaca saat ini = interval pertama
    sekarang = forecasts[0] if forecasts else {}

    return {
        "kota": city.get("name", "Unknown"),
        "negara": city.get("country", ""),
        "sekarang": sekarang,
        "prakiraan": forecasts,
        "terakhir_diperbarui": datetime.now().isoformat(),
    }


def cek_hujan_akan_datang(data: dict | None, jam_ke_depan: int = 2) -> dict:
    """
    Cek apakah hujan signifikan (deras/lama) diprediksi dalam N jam ke depan.
    Jika hujan hanya ringan dan durasi singkat, penyiraman pompa TIDAK ditunda.
    Return dict dengan info: akan_hujan (bool), detail prakiraan.
    """
    if data is None:
        return {
            "tersedia": False,
            "akan_hujan": False,
            "pesan": "Data cuaca tidak tersedia",
        }

    batas_waktu_awal = datetime.now() + timedelta(hours=jam_ke_depan)
    batas_waktu_lama = datetime.now() + timedelta(hours=9) # window 9 jam untuk cek "lama"

    hujan_segera = []
    hujan_lanjutan = []

    # Saring item yang sudah lewat (lebih dari 15 menit) agar tidak macet di "0 menit"
    batas_waktu_lampau = datetime.now() - timedelta(minutes=15)

    for item in data.get("prakiraan", []):
        waktu = datetime.fromisoformat(item["waktu"])
        if waktu < batas_waktu_lampau:
            continue
        if waktu > batas_waktu_lama:
            break
            
        if item["adalah_hujan"]:
            if waktu <= batas_waktu_awal:
                hujan_segera.append(item)
            hujan_lanjutan.append(item)

    if hujan_segera:
        terdekat = hujan_segera[0]
        waktu_hujan = datetime.fromisoformat(terdekat["waktu"])
        selisih_menit = int((waktu_hujan - datetime.now()).total_seconds() / 60)
        kode = terdekat["kode_cuaca"]
        
        # 2xx: Badai petir (Deras)
        # 3xx: Gerimis (Ringan)
        # 500: Hujan ringan (Ringan)
        # 501+: Hujan sedang - ekstrim (Deras)
        is_deras = (200 <= kode < 300) or (501 <= kode < 600)
        
        # Jika ada >= 2 interval berurutan/berdekatan (6+ jam) yang hujan, dianggap "Lama"
        is_lama = len(hujan_lanjutan) >= 2 

        if is_deras or is_lama:
            alasan = "lebat" if is_deras else ("lama/awet" if is_lama else "")
            return {
                "tersedia": True,
                "akan_hujan": True, # TUNDA POMPA
                "jumlah_interval_hujan": len(hujan_lanjutan),
                "prakiraan_terdekat": terdekat,
                "menit_hingga_hujan": max(0, selisih_menit),
                "pesan": f"Hujan {alasan} diprediksi dalam ~{max(0, selisih_menit)} menit ({terdekat['deskripsi']})",
            }
        else:
            return {
                "tersedia": True,
                "akan_hujan": False,  # LANJUT SIRAM (karena hujan ringan & singkat)
                "pesan": f"Hujan diprediksi MENDUNG/RINGAN saja ({terdekat['deskripsi']}), penyiraman otomatis tetap akan berjalan."
            }

    return {
        "tersedia": True,
        "akan_hujan": False,
        "pesan": f"Tidak ada prakiraan cuaca buruk dalam {jam_ke_depan} jam ke depan",
    }


def get_cuaca_sekarang(data: dict | None) -> dict:
    """Ambil ringkasan cuaca saat ini dari cache."""
    if data is None:
        return {
            "tersedia": False,
            "pesan": "Gagal mengambil data cuaca. Periksa koneksi internet atau pastikan OPENWEATHER_API_KEY di .env valid/aktif.",
        }

    sekarang = data.get("sekarang", {})
    return {
        "tersedia": True,
        "kota": data.get("kota", ""),
        "suhu": sekarang.get("suhu"),
        "kelembaban": sekarang.get("kelembaban"),
        "kondisi": sekarang.get("kondisi", ""),
        "deskripsi": sekarang.get("deskripsi", ""),
        "ikon": sekarang.get("ikon", ""),
        "angin": sekarang.get("angin_kecepatan", 0),
        "adalah_hujan": sekarang.get("adalah_hujan", False),
        "terakhir_diperbarui": data.get("terakhir_diperbarui", ""),
    }
