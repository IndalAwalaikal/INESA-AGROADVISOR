"""
Jadwal Service — CRUD + Eksekusi Jadwal Pompa Terjadwal

Mengelola jadwal penyiraman rutin (cron-like).
Petani bisa mengatur pompa menyala pada jam tertentu selama durasi tertentu,
terlepas dari kondisi sensor.
"""
from datetime import datetime, time as dtime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# ── State pompa terjadwal (in-memory tracker) ────────────────────────────────
_jadwal_aktif = {
    "sedang_berjalan": False,
    "jadwal_id": None,
    "nyala_sejak": None,
    "durasi_menit": 0,
}


def get_semua_jadwal(db: Session) -> list:
    """Ambil semua jadwal dari database."""
    rows = db.execute(text("""
        SELECT id, jam, durasi_menit, hari, aktif, dibuat_pada
        FROM jadwal_pompa
        ORDER BY jam ASC
    """)).fetchall()

    return [
        {
            "id":            row[0],
            "jam":           str(row[1]),
            "durasi_menit":  row[2],
            "hari":          row[3],
            "aktif":         bool(row[4]),
            "dibuat_pada":   str(row[5]),
        }
        for row in rows
    ]


def tambah_jadwal(db: Session, jam: str, durasi_menit: int, hari: str = "semua") -> dict:
    """Tambah jadwal pompa baru."""
    result = db.execute(text("""
        INSERT INTO jadwal_pompa (jam, durasi_menit, hari, aktif)
        VALUES (:jam, :durasi, :hari, TRUE)
    """), {"jam": jam, "durasi": durasi_menit, "hari": hari})
    db.commit()
    return {
        "id": result.lastrowid,
        "jam": jam,
        "durasi_menit": durasi_menit,
        "hari": hari,
        "aktif": True,
    }


def hapus_jadwal(db: Session, jadwal_id: int) -> bool:
    """Hapus jadwal berdasarkan ID."""
    result = db.execute(
        text("DELETE FROM jadwal_pompa WHERE id = :id"),
        {"id": jadwal_id},
    )
    db.commit()
    return result.rowcount > 0


def toggle_jadwal(db: Session, jadwal_id: int, aktif: bool) -> bool:
    """Aktifkan atau nonaktifkan jadwal."""
    result = db.execute(
        text("UPDATE jadwal_pompa SET aktif = :aktif WHERE id = :id"),
        {"aktif": aktif, "id": jadwal_id},
    )
    db.commit()
    return result.rowcount > 0


def get_jadwal_state() -> dict:
    """Ambil state jadwal yang sedang berjalan (jika ada)."""
    return dict(_jadwal_aktif)


def _to_time(val):
    """Konversi timedelta ke time jika perlu (MySQL TIME → Python timedelta)."""
    if isinstance(val, timedelta):
        total_seconds = int(val.total_seconds())
        h = (total_seconds // 3600) % 24
        m = (total_seconds % 3600) // 60
        return dtime(h, m)
    if isinstance(val, str):
        parts = val.split(":")
        return dtime(int(parts[0]), int(parts[1]))
    return val


def cek_dan_eksekusi_jadwal(db: Session) -> dict | None:
    """
    Dipanggil setiap 1 menit oleh scheduler.
    Cek apakah ada jadwal yang cocok dengan waktu sekarang.
    Jika ya, nyalakan pompa dan catat log.
    """
    from app.services.pompa_service import get_konfigurasi, _state_pompa, _set_state, catat_log_pompa
    from app.services.sensor_service import get_atau_buat_sesi

    cfg = get_konfigurasi(db)
    if cfg["mode"] != "terjadwal":
        return None

    # Jika pompa sudah nyala karena jadwal, jangan double-trigger
    if _jadwal_aktif["sedang_berjalan"]:
        return None

    now = datetime.now()
    jam_sekarang = now.time()
    hari_sekarang = now.strftime("%A").lower()
    nama_hari_id = {
        "monday": "senin", "tuesday": "selasa", "wednesday": "rabu",
        "thursday": "kamis", "friday": "jumat", "saturday": "sabtu", "sunday": "minggu",
    }
    hari_id = nama_hari_id.get(hari_sekarang, hari_sekarang)

    rows = db.execute(text("""
        SELECT id, jam, durasi_menit, hari
        FROM jadwal_pompa
        WHERE aktif = TRUE
    """)).fetchall()

    for row in rows:
        jadwal_id = row[0]
        jam_jadwal = _to_time(row[1])
        durasi = row[2]
        hari = row[3] or "semua"

        # Cek hari
        if hari != "semua" and hari_id not in hari.lower():
            continue

        # Cek apakah jam sekarang cocok (toleransi 1 menit)
        jadwal_menit = jam_jadwal.hour * 60 + jam_jadwal.minute
        sekarang_menit = jam_sekarang.hour * 60 + jam_sekarang.minute

        if jadwal_menit == sekarang_menit:
            # Trigger pompa!
            sesi_id = get_atau_buat_sesi()
            alasan = f"Jadwal terjadwal: {jam_jadwal.strftime('%H:%M')} selama {durasi} menit"

            _set_state("nyala", alasan)
            _state_pompa["override_manual"] = False
            catat_log_pompa(db, sesi_id, "nyala", "terjadwal", alasan)

            _jadwal_aktif["sedang_berjalan"] = True
            _jadwal_aktif["jadwal_id"] = jadwal_id
            _jadwal_aktif["nyala_sejak"] = now
            _jadwal_aktif["durasi_menit"] = durasi

            logger.info(f"Pompa terjadwal NYALA: {alasan}")
            return {"aksi": "dinyalakan", "alasan": alasan, "jadwal_id": jadwal_id}

    return None


def cek_dan_matikan_jadwal(db: Session) -> dict | None:
    """
    Dipanggil setiap 1 menit oleh scheduler.
    Cek apakah pompa terjadwal sudah melewati durasi dan perlu dimatikan.
    """
    from app.services.pompa_service import _set_state, catat_log_pompa
    from app.services.sensor_service import get_atau_buat_sesi

    if not _jadwal_aktif["sedang_berjalan"]:
        return None

    now = datetime.now()
    nyala_sejak = _jadwal_aktif["nyala_sejak"]
    durasi_target = _jadwal_aktif["durasi_menit"]

    if nyala_sejak is None:
        return None

    durasi_berlalu = int((now - nyala_sejak).total_seconds() / 60)

    if durasi_berlalu >= durasi_target:
        sesi_id = get_atau_buat_sesi()
        alasan = f"Jadwal terjadwal selesai setelah {durasi_berlalu} menit"

        _set_state("mati", alasan)
        catat_log_pompa(db, sesi_id, "mati", "terjadwal", alasan, durasi_menit=durasi_berlalu)

        _jadwal_aktif["sedang_berjalan"] = False
        _jadwal_aktif["jadwal_id"] = None
        _jadwal_aktif["nyala_sejak"] = None
        _jadwal_aktif["durasi_menit"] = 0

        logger.info(f"Pompa terjadwal MATI: {alasan}")
        return {"aksi": "dimatikan", "alasan": alasan}

    return None
