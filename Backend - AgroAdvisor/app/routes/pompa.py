from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.services.sensor_service import baca_sensor_json, get_atau_buat_sesi
from app.services.pompa_service import (
    evaluasi_pompa,
    kontrol_manual,
    kembalikan_ke_otomatis,
    get_status_pompa,
    update_konfigurasi,
    ambil_riwayat_pompa,
)

router = APIRouter(prefix="/api/pompa", tags=["Kontrol Pompa Otomatis"])


# ─── Request Models ───────────────────────────────────────────────────────────

class ManualKontrolRequest(BaseModel):
    perintah: str  = Field(..., description="nyala | mati")
    alasan:   Optional[str] = "Override manual oleh operator"


class UpdateKonfigurasiRequest(BaseModel):
    suhu_nyala:          Optional[float] = Field(None, description="Nyalakan jika suhu > nilai ini (°C)")
    durasi_panas_menit:  Optional[int]   = Field(None, description="Sudah panas selama X menit baru nyala")
    kelembaban_nyala:    Optional[float] = Field(None, description="Nyalakan jika kelembaban tanah < nilai ini (%)")
    maks_durasi_menit:   Optional[int]   = Field(None, description="Maks pompa menyala (menit)")
    jeda_setelah_menit:  Optional[int]   = Field(None, description="Jeda setelah mati sebelum bisa nyala lagi")
    aktif_jam_mulai:     Optional[str]   = Field(None, description="Format HH:MM:SS — mulai jam berapa pompa boleh nyala")
    aktif_jam_selesai:   Optional[str]   = Field(None, description="Format HH:MM:SS — batas jam pompa boleh nyala")
    mode:                Optional[str]   = Field(None, description="otomatis | manual | terjadwal | nonaktif")


class TambahJadwalRequest(BaseModel):
    jam:           str = Field(..., description="Format HH:MM — jam penyiraman")
    durasi_menit:  int = Field(15, ge=1, le=120, description="Durasi penyiraman dalam menit")
    hari:          Optional[str] = Field("semua", description="semua | senin,selasa,... (pisahkan koma)")


class ToggleJadwalRequest(BaseModel):
    aktif: bool = Field(..., description="True untuk aktifkan, False untuk nonaktifkan")


# ─────────────────────────────────────────────────────────────────────────────
# 1. STATUS & EVALUASI OTOMATIS
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="Status pompa saat ini + evaluasi otomatis dari sensor",
)
def get_status(db: Session = Depends(get_db)):
    """
    Baca status pompa terkini dan jalankan evaluasi otomatis berdasarkan sensor.

    Dashboard publik memanggil endpoint ini secara berkala (polling).
    Setiap kali dipanggil, rule engine mengevaluasi kondisi sensor dan
    memutuskan apakah pompa perlu dinyalakan atau dimatikan.

    **State machine pompa:**
    - `mati` → kondisi normal, tidak perlu irigasi
    - `nyala` → sedang menyiram otomatis
    - `manual_nyala` → dinyalakan paksa oleh operator
    - `manual_mati` → dimatikan paksa oleh operator
    - `nonaktif` → pompa dinonaktifkan dari konfigurasi
    """
    sesi_id = get_atau_buat_sesi()

    # Baca sensor terkini
    try:
        from app.services.weather_service import _cache, get_cuaca_sekarang
        cuaca_sekarang = get_cuaca_sekarang(_cache.get("data"))
        hujan = cuaca_sekarang.get("adalah_hujan", False)
        
        raw     = baca_sensor_json()
        sensors = raw.get("sensors", {})
        suhu    = sensors.get("suhu_udara", 30.0)
        kelembaban_tanah = sensors.get("kelembaban_tanah", 50.0)
    except FileNotFoundError:
        suhu             = 30.0
        kelembaban_tanah = 50.0
        hujan            = False

    # Jalankan rule engine
    hasil_evaluasi = evaluasi_pompa(
        db               =db,
        sesi_id          =sesi_id,
        suhu_udara       =suhu,
        kelembaban_tanah =kelembaban_tanah,
    )

    # Gabungkan dengan info lengkap state pompa
    status_lengkap = get_status_pompa(db)

    return {
        "sukses":          True,
        "evaluasi":        hasil_evaluasi,
        "status_lengkap":  status_lengkap,
        "data_sensor": {
            "suhu_udara":       suhu,
            "kelembaban_tanah": kelembaban_tanah,
            "hujan_terdeteksi": hujan,
        },
        "diperbarui_pada": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. KONTROL MANUAL
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/manual",
    summary="Override manual — operator nyalakan atau matikan pompa",
)
async def post_kontrol_manual(
    request: ManualKontrolRequest,
    db:      Session = Depends(get_db),
):
    """
    Operator mengambil alih kontrol pompa dari dashboard.
    Perintah manual menggantikan logika otomatis.

    Gunakan `POST /pompa/otomatis` untuk mengembalikan ke mode otomatis.
    """
    sesi_id = get_atau_buat_sesi()
    hasil   = kontrol_manual(db, sesi_id, request.perintah, request.alasan)

    if not hasil.get("sukses"):
        raise HTTPException(status_code=400, detail=hasil.get("error"))

    from app.websocket_manager import manager
    if manager.jumlah_client > 0:
        await manager.kirim_update_pompa(
            status=hasil["status_baru"],
            alasan=hasil["alasan"],
            data_sensor={}
        )

    return hasil


@router.post(
    "/otomatis",
    summary="Kembalikan pompa ke mode otomatis setelah override manual",
)
def post_kembalikan_otomatis(db: Session = Depends(get_db)):
    """Kembalikan kontrol pompa ke rule engine otomatis."""
    sesi_id = get_atau_buat_sesi()
    return kembalikan_ke_otomatis(db, sesi_id)


# ─────────────────────────────────────────────────────────────────────────────
# 3. KONFIGURASI THRESHOLD
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/konfigurasi",
    summary="Lihat konfigurasi threshold pompa saat ini",
)
def get_konfigurasi_pompa(db: Session = Depends(get_db)):
    """
    Tampilkan semua threshold dan pengaturan pompa yang aktif.
    Nilai ini bisa diubah melalui `PUT /pompa/konfigurasi`.
    """
    from app.services.pompa_service import get_konfigurasi
    cfg = get_konfigurasi(db)
    return {"sukses": True, "konfigurasi": cfg}


@router.put(
    "/konfigurasi",
    summary="Update threshold dan pengaturan pompa",
)
def put_konfigurasi_pompa(
    request: UpdateKonfigurasiRequest,
    db:      Session = Depends(get_db),
):
    """
    Update konfigurasi threshold pompa dari dashboard.

    **Contoh penggunaan:**
    - Musim kemarau panjang → turunkan `suhu_nyala` ke 31°C
    - Tanaman muda (butuh lebih banyak air) → naikkan `kelembaban_nyala` ke 50%
    - Nonaktifkan pompa saat maintenance → set `mode` ke `nonaktif`
    """
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    berhasil = update_konfigurasi(db, data)

    if not berhasil:
        raise HTTPException(status_code=400, detail="Tidak ada field valid yang diupdate")

    from app.services.pompa_service import get_konfigurasi
    return {
        "sukses":         True,
        "pesan":          "Konfigurasi pompa berhasil diperbarui",
        "konfigurasi_baru": get_konfigurasi(db),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. RIWAYAT
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/riwayat",
    summary="Riwayat aktivitas pompa",
)
def get_riwayat_pompa(
    limit: int     = Query(30, ge=1, le=200),
    db:    Session = Depends(get_db),
):
    """
    Log semua aktivitas pompa: kapan nyala, kapan mati, siapa yang trigger,
    kondisi suhu dan kelembaban saat itu, dan berapa lama menyala.
    """
    data = ambil_riwayat_pompa(db, limit)
    return {"sukses": True, "total": len(data), "data": data}


# ─────────────────────────────────────────────────────────────────────────────
# 5. JADWAL POMPA TERJADWAL
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/jadwal",
    summary="Daftar semua jadwal penyiraman terjadwal",
)
def get_jadwal_pompa(db: Session = Depends(get_db)):
    """Ambil semua jadwal pompa terjadwal."""
    from app.services.jadwal_service import get_semua_jadwal
    data = get_semua_jadwal(db)
    return {"sukses": True, "total": len(data), "data": data}


@router.post(
    "/jadwal",
    summary="Tambah jadwal penyiraman baru",
)
def post_jadwal_pompa(
    request: TambahJadwalRequest,
    db:      Session = Depends(get_db),
):
    """Tambah jadwal penyiraman rutin baru (misal: 06:00 selama 15 menit)."""
    from app.services.jadwal_service import tambah_jadwal
    hasil = tambah_jadwal(db, request.jam, request.durasi_menit, request.hari or "semua")
    return {"sukses": True, "pesan": "Jadwal berhasil ditambahkan", "data": hasil}


@router.delete(
    "/jadwal/{jadwal_id}",
    summary="Hapus jadwal penyiraman",
)
def delete_jadwal_pompa(
    jadwal_id: int,
    db:        Session = Depends(get_db),
):
    """Hapus jadwal penyiraman berdasarkan ID."""
    from app.services.jadwal_service import hapus_jadwal
    berhasil = hapus_jadwal(db, jadwal_id)
    if not berhasil:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    return {"sukses": True, "pesan": "Jadwal berhasil dihapus"}


@router.put(
    "/jadwal/{jadwal_id}/toggle",
    summary="Aktifkan atau nonaktifkan jadwal",
)
def put_toggle_jadwal(
    jadwal_id: int,
    request:   ToggleJadwalRequest,
    db:        Session = Depends(get_db),
):
    """Toggle aktif/nonaktif jadwal penyiraman."""
    from app.services.jadwal_service import toggle_jadwal
    berhasil = toggle_jadwal(db, jadwal_id, request.aktif)
    if not berhasil:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    return {"sukses": True, "pesan": f"Jadwal {'diaktifkan' if request.aktif else 'dinonaktifkan'}"}


# ─────────────────────────────────────────────────────────────────────────────
# 6. EKSPOR CSV
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/riwayat/export/csv", summary="Export riwayat pompa ke CSV")
def get_export_pompa_csv(db: Session = Depends(get_db)):
    """Download semua riwayat aktivitas pompa dalam format CSV."""
    from app.services.export_service import export_riwayat_pompa_csv
    from fastapi.responses import Response as FileResponse
    csv_bytes = export_riwayat_pompa_csv(db)
    return FileResponse(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=riwayat_pompa_{datetime.now().strftime('%Y%m%d')}.csv"}
    )