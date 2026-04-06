from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.sensor_service import update_sensor_iot, get_atau_buat_sesi
from app.services.pompa_service import evaluasi_pompa
from app.websocket_manager import manager

router = APIRouter(prefix="/api/iot", tags=["IoT"])

class IoTSensorRequest(BaseModel):
    device_id: str
    suhu_udara: float
    kelembaban_udara: float
    ph_tanah: float
    nitrogen: float
    fosfor: float
    kalium: float
    kelembaban_tanah: float
    hujan_terdeteksi: bool

@router.post("/sensor")
async def post_sensor_iot(req: IoTSensorRequest, db: Session = Depends(get_db)):
    # 1. Update state sensor in-memory
    update_sensor_iot(req.model_dump())
    
    # 2. Ambil sesi aktif
    sesi_id = get_atau_buat_sesi()
    
    # 3. Jalankan evaluasi pompa otomatis (Rule Engine)
    hasil = evaluasi_pompa(
        db=db,
        sesi_id=sesi_id,
        suhu_udara=req.suhu_udara,
        kelembaban_tanah=req.kelembaban_tanah,
        hujan_terdeteksi=req.hujan_terdeteksi
    )
    
    # 4. Broadcast ke Dashboard via WebSocket
    await manager.broadcast({
        "type": "sensor_update",
        "data": {
            **req.model_dump(),
            "status_pompa": hasil["status_pompa"],
            "alasan": hasil["alasan"]
        }
    })
    
    # 5. Berikan respon balik ke ESP32 (perintah pompa)
    # ESP32 biasanya mengharapkan format sederhana untuk hemat bandwidth
    pump_command = "on" if hasil["status_pompa"] in ("nyala", "manual_nyala") else "off"
    
    return {
        "status": "ok",
        "pump": pump_command,
        "sesi_id": sesi_id,
        "mode": hasil.get("status_pompa")
    }
