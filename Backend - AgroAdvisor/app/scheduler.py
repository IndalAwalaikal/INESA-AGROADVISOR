"""
Background Scheduler — AgriSmart AI

Menjalankan task secara berkala di background tanpa menunggu request dari frontend:
1. Setiap 30 detik: baca sensor → evaluasi pompa → broadcast ke semua client
2. Setiap 5 menit: cek kondisi kritis → kirim alert jika ada

Ini menggantikan polling dari frontend dan memastikan pompa dievaluasi
bahkan saat tidak ada yang membuka dashboard.
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Scheduler global
scheduler = AsyncIOScheduler()
_scheduler_running = False


async def _task_evaluasi_sensor_dan_pompa():
    """
    Task utama yang berjalan setiap 30 detik:
    1. Baca data sensor dari JSON (nanti dari MQTT IoT)
    2. Evaluasi kondisi tanah
    3. Jalankan rule engine pompa
    4. Broadcast semua update ke client WebSocket
    """
    from app.database import SessionLocal
    from app.services.sensor_service import baca_sensor_json, get_atau_buat_sesi, evaluasi_kondisi_tanah
    from app.services.pompa_service import evaluasi_pompa, get_status_pompa
    from app.services.db_service import simpan_log_sensor, simpan_sesi
    from app.websocket_manager import manager

    db = SessionLocal()
    try:
        # 1. Baca sensor
        try:
            raw     = baca_sensor_json()
            sensors = raw.get("sensors", {})
        except FileNotFoundError:
            logger.warning("File sensor tidak ditemukan, skip evaluasi")
            return

        sesi_id   = get_atau_buat_sesi()
        device_id = raw.get("device_id", "scheduler")
        lokasi    = raw.get("lokasi", "Tidak diketahui")

        # 2. Evaluasi kondisi tanah
        status_tanah = evaluasi_kondisi_tanah(
            ph=sensors.get("ph_tanah", 7.0),
            n =sensors.get("nitrogen", 0),
            p =sensors.get("fosfor", 0),
            k =sensors.get("kalium", 0),
        )

        # 3. Simpan sesi dulu (parent), BARU simpan log sensor (child)
        simpan_sesi(
            db=db, sesi_id=sesi_id, device_id=device_id, lokasi=lokasi,
            jenis_tanaman="", fase_tumbuh="", luas_lahan=1.0, sensor_data=raw,
        )
        simpan_log_sensor(db, sesi_id, raw, device_id)

        # 4. Evaluasi pompa
        hasil_pompa = evaluasi_pompa(
            db               =db,
            sesi_id          =sesi_id,
            suhu_udara       =sensors.get("suhu_udara", 30.0),
            kelembaban_tanah =sensors.get("kelembaban_tanah", 50.0),
        )

        # 5. Broadcast update sensor ke semua client WebSocket
        if manager.jumlah_client > 0:
            await manager.kirim_update_sensor(
                sensor_data  ={
                    "device_id":         raw.get("device_id"),
                    "lokasi":            raw.get("lokasi"),
                    "ph_tanah":          sensors.get("ph_tanah"),
                    "nitrogen":          sensors.get("nitrogen"),
                    "fosfor":            sensors.get("fosfor"),
                    "kalium":            sensors.get("kalium"),
                    "suhu_udara":        sensors.get("suhu_udara"),
                    "kelembaban_udara":  sensors.get("kelembaban_udara"),
                    "kelembaban_tanah":  sensors.get("kelembaban_tanah"),
                    "hujan_terdeteksi":  sensors.get("hujan_terdeteksi"),
                },
                status_tanah=status_tanah,
            )

            # Broadcast status pompa jika ada perubahan aksi
            if hasil_pompa.get("aksi") != "tidak_ada":
                await manager.kirim_update_pompa(
                    status      =hasil_pompa["status_pompa"],
                    alasan      =hasil_pompa["alasan"],
                    data_sensor ={
                        "suhu_udara":       sensors.get("suhu_udara"),
                        "kelembaban_tanah": sensors.get("kelembaban_tanah"),
                    },
                )

    except Exception as e:
        logger.error(f"Error di task evaluasi sensor: {e}")
    finally:
        db.close()


async def _task_cek_kondisi_kritis():
    """
    Task yang berjalan setiap 5 menit:
    Cek kondisi tanah kritis dan kirim alert ke dashboard jika ada.

    Kondisi kritis:
    - pH sangat asam (< 5.0) atau sangat basa (> 8.0)
    - Nitrogen sangat rendah (< 20 mg/kg)
    - Suhu ekstrem (> 38°C)
    - Kelembaban tanah sangat rendah (< 20%)
    """
    from app.services.sensor_service import baca_sensor_json
    from app.websocket_manager import manager

    if manager.jumlah_client == 0:
        return  # Tidak ada yang menonton, skip

    try:
        raw     = baca_sensor_json()
        sensors = raw.get("sensors", {})
        alerts  = []

        ph   = sensors.get("ph_tanah")
        n    = sensors.get("nitrogen")
        suhu = sensors.get("suhu_udara")
        hum  = sensors.get("kelembaban_tanah")

        if ph is not None:
            if ph < 5.0:
                alerts.append({"level": "critical", "pesan": f"pH tanah sangat asam ({ph}) — tanaman berisiko stres"})
            elif ph > 8.0:
                alerts.append({"level": "critical", "pesan": f"pH tanah sangat basa ({ph}) — hara sulit diserap tanaman"})

        if n is not None and n < 20:
            alerts.append({"level": "warning", "pesan": f"Nitrogen sangat rendah ({n} mg/kg) — tanaman perlu pupuk N segera"})

        if suhu is not None and suhu > 38:
            alerts.append({"level": "warning", "pesan": f"Suhu ekstrem ({suhu}°C) — perhatikan kondisi tanaman"})

        if hum is not None and hum < 20:
            alerts.append({"level": "critical", "pesan": f"Kelembaban tanah kritis ({hum}%) — tanaman terancam layu"})

        for alert in alerts:
            await manager.kirim_alert(
                level=alert["level"],
                pesan=alert["pesan"],
                data ={"sensor": sensors},
            )

    except Exception as e:
        logger.error(f"Error di task cek kondisi kritis: {e}")


async def _task_cleanup_harian():
    """
    Task harian yang berjalan setiap tengah malam:
    Hapus data riwayat yang lebih tua dari 6 bulan.
    """
    from app.database import SessionLocal
    from app.services.cleanup_service import jalankan_cleanup_riwayat

    db = SessionLocal()
    try:
        jalankan_cleanup_riwayat(db, bulan=6)
    finally:
        db.close()


async def _task_cek_jadwal_pompa():
    """
    Task yang berjalan setiap 1 menit:
    Cek apakah ada jadwal pompa terjadwal yang harus dieksekusi sekarang.
    """
    from app.database import SessionLocal
    from app.services.jadwal_service import cek_dan_eksekusi_jadwal
    from app.services.pompa_service import get_status_pompa
    from app.websocket_manager import manager

    db = SessionLocal()
    try:
        hasil = cek_dan_eksekusi_jadwal(db)
        if hasil and manager.jumlah_client > 0:
            await manager.kirim_update_pompa(
                status="nyala",
                alasan=hasil["alasan"],
                data_sensor={},
            )
    except Exception as e:
        logger.error(f"Error di task cek jadwal pompa: {e}")
    finally:
        db.close()


async def _task_matikan_pompa_terjadwal():
    """
    Task yang berjalan setiap 1 menit:
    Cek apakah pompa terjadwal sudah melewati durasi dan perlu dimatikan.
    """
    from app.database import SessionLocal
    from app.services.jadwal_service import cek_dan_matikan_jadwal
    from app.websocket_manager import manager

    db = SessionLocal()
    try:
        hasil = cek_dan_matikan_jadwal(db)
        if hasil and manager.jumlah_client > 0:
            await manager.kirim_update_pompa(
                status="mati",
                alasan=hasil["alasan"],
                data_sensor={},
            )
    except Exception as e:
        logger.error(f"Error di task matikan pompa terjadwal: {e}")
    finally:
        db.close()


async def _task_update_cuaca():
    """
    Task yang berjalan setiap 15 menit:
    Refresh cache prakiraan cuaca dari OpenWeatherMap.
    """
    from app.services.weather_service import fetch_prakiraan_cuaca
    try:
        await fetch_prakiraan_cuaca()
        logger.debug("Cache cuaca di-refresh")
    except Exception as e:
        logger.error(f"Error di task update cuaca: {e}")


def start_scheduler():
    """Mulai semua background task scheduler."""
    global _scheduler_running
    if _scheduler_running:
        return

    # Task 1: Evaluasi sensor + pompa setiap 30 detik
    scheduler.add_job(
        _task_evaluasi_sensor_dan_pompa,
        trigger   =IntervalTrigger(seconds=30),
        id        ="evaluasi_sensor_pompa",
        name      ="Evaluasi Sensor & Pompa",
        replace_existing=True,
        max_instances=1,  # Pastikan tidak overlap
    )

    # Task 2: Cek kondisi kritis setiap 5 menit
    scheduler.add_job(
        _task_cek_kondisi_kritis,
        trigger   =IntervalTrigger(minutes=5),
        id        ="cek_kondisi_kritis",
        name      ="Cek Kondisi Kritis",
        replace_existing=True,
        max_instances=1,
    )

    # Task 3: Cleanup riwayat harian (setiap jam 00:00)
    scheduler.add_job(
        _task_cleanup_harian,
        trigger   =CronTrigger(hour=0, minute=0),
        id        ="cleanup_harian",
        name      ="Cleanup Riwayat Hama & Pupuk > 6 Bulan",
        replace_existing=True,
    )

    # Task 4: Cek jadwal pompa terjadwal setiap 1 menit
    scheduler.add_job(
        _task_cek_jadwal_pompa,
        trigger   =IntervalTrigger(minutes=1),
        id        ="cek_jadwal_pompa",
        name      ="Cek Jadwal Pompa Terjadwal",
        replace_existing=True,
        max_instances=1,
    )

    # Task 5: Matikan pompa terjadwal jika durasi habis (setiap 1 menit)
    scheduler.add_job(
        _task_matikan_pompa_terjadwal,
        trigger   =IntervalTrigger(minutes=1),
        id        ="matikan_pompa_terjadwal",
        name      ="Matikan Pompa Terjadwal",
        replace_existing=True,
        max_instances=1,
    )

    # Task 6: Update cache prakiraan cuaca setiap 15 menit
    scheduler.add_job(
        _task_update_cuaca,
        trigger   =IntervalTrigger(minutes=15),
        id        ="update_cuaca",
        name      ="Update Cache Prakiraan Cuaca",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    _scheduler_running = True
    logger.info("Scheduler started: evaluasi sensor 30s, cek kritis 5m, jadwal 1m, cuaca 15m")


def stop_scheduler():
    """Hentikan scheduler saat server shutdown."""
    global _scheduler_running
    if _scheduler_running and scheduler.running:
        scheduler.shutdown(wait=False)
        _scheduler_running = False