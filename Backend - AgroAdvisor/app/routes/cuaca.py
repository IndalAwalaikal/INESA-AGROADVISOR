"""
Route Cuaca — Prakiraan Cuaca Lokal via OpenWeatherMap API

Endpoint:
- GET /api/cuaca/sekarang   — cuaca saat ini
- GET /api/cuaca/prakiraan  — prakiraan 24 jam ke depan
- GET /api/cuaca/hujan-alert — apakah hujan diprediksi dalam 2 jam
"""
from fastapi import APIRouter, Query

from app.services.weather_service import (
    fetch_prakiraan_cuaca,
    cek_hujan_akan_datang,
    get_cuaca_sekarang,
)

router = APIRouter(prefix="/api/cuaca", tags=["Prakiraan Cuaca"])


@router.get(
    "/sekarang",
    summary="Cuaca saat ini dari OpenWeatherMap",
)
async def get_cuaca_sekarang_endpoint():
    """Ambil ringkasan cuaca saat ini."""
    data = await fetch_prakiraan_cuaca()
    return {"sukses": True, "cuaca": get_cuaca_sekarang(data)}


@router.get(
    "/prakiraan",
    summary="Prakiraan cuaca 48 jam ke depan",
)
async def get_prakiraan():
    """Ambil prakiraan cuaca per 3 jam, hingga 48 jam ke depan."""
    data = await fetch_prakiraan_cuaca()
    if data is None:
        return {
            "sukses": False,
            "pesan": "Data cuaca tidak tersedia. Tambahkan OPENWEATHER_API_KEY ke .env",
        }
    return {
        "sukses": True,
        "kota": data.get("kota", ""),
        "prakiraan": data.get("prakiraan", []),
        "terakhir_diperbarui": data.get("terakhir_diperbarui", ""),
    }


@router.get(
    "/hujan-alert",
    summary="Cek apakah hujan diprediksi dalam N jam ke depan",
)
async def get_hujan_alert(
    jam: int = Query(2, ge=1, le=24, description="Cek hujan N jam ke depan"),
):
    """Cek apakah akan hujan dalam N jam ke depan untuk keputusan pompa."""
    data = await fetch_prakiraan_cuaca()
    alert = cek_hujan_akan_datang(data, jam_ke_depan=jam)
    return {"sukses": True, **alert}
