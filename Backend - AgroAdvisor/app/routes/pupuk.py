from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.database import get_db
from app.models.schemas import (
    RekomendasiPupukRequest,
    Alur2SaranTanamanDanPupukRequest,
    ResetSesiRequest,
    FeedbackRequest,
    StatusSensor,
)
from app.services.sensor_service import (
    baca_sensor_json,
    get_atau_buat_sesi,
    reset_sesi,
    get_info_sesi,
    evaluasi_kondisi_tanah,
)
from app.services.ai_service import (
    generate_rekomendasi_pupuk,
    generate_saran_tanaman,
    generate_alur2_saran_tanaman_dan_pupuk,
    PROFIL_TANAMAN,
)
from app.services.db_service import (

    simpan_sesi,
    simpan_log_sensor,
    simpan_rekomendasi_pupuk,
    tandai_sesi_reset,
    ambil_riwayat_untuk_pembelajaran,
    ambil_riwayat_rekomendasi,
    simpan_feedback,
    ambil_statistik,
    ambil_rekomendasi_pupuk_by_id,
)
from app.services.pdf_service import generate_pupuk_pdf
from fastapi.responses import Response

router = APIRouter(prefix="/api/pupuk", tags=["Rekomendasi Pupuk"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. STATUS SENSOR
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/sensor/status",
    response_model=StatusSensor,
    summary="Data sensor terkini beserta status tiap parameter",
)
def get_status_sensor():
    """
    Baca data sensor terkini dari file JSON (pengganti IoT).
    Dashboard publik memanggil endpoint ini secara berkala untuk monitoring real-time.
    Saat IoT sudah tersambung, cukup ganti `baca_sensor_json()` dengan pembacaan MQTT.
    """
    try:
        from app.services.weather_service import _cache, get_cuaca_sekarang
        cuaca_aktif = get_cuaca_sekarang(_cache.get("data"))
        hujan = cuaca_aktif.get("adalah_hujan", False)
        
        data    = baca_sensor_json()
        sensors = data.get("sensors", {})
        sesi_id = get_atau_buat_sesi()
        status  = evaluasi_kondisi_tanah(
            ph=sensors.get("ph_tanah", 7.0),
            n=sensors.get("nitrogen", 0),
            p=sensors.get("fosfor", 0),
            k=sensors.get("kalium", 0),
        )
        return StatusSensor(
            device_id        =data.get("device_id", "unknown"),
            lokasi           =data.get("lokasi", "Tidak diketahui"),
            sesi_id          =sesi_id,
            timestamp        =data.get("timestamp", datetime.now().isoformat()),
            ph_tanah         =sensors.get("ph_tanah"),
            nitrogen         =sensors.get("nitrogen"),
            fosfor           =sensors.get("fosfor"),
            kalium           =sensors.get("kalium"),
            suhu_udara       =sensors.get("suhu_udara"),
            kelembaban_udara =sensors.get("kelembaban_udara"),
            kelembaban_tanah =sensors.get("kelembaban_tanah"),
            hujan_terdeteksi =hujan,
            **status,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 2. SARAN TANAMAN  (sebelum user memilih)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/saran-tanaman",
    summary="AI: Tanaman apa yang cocok untuk kondisi tanah ini?",
)
async def get_saran_tanaman():
    """
    Berdasarkan kondisi tanah dari sensor, AI merekomendasikan tanaman apa
    yang paling cocok. Ditampilkan di dashboard **sebelum** user memilih tanaman,
    sebagai panduan awal agar pilihan lebih tepat.

    User tetap bebas memilih tanaman apapun — endpoint ini hanya panduan, bukan kewajiban.
    """
    try:
        data    = baca_sensor_json()
        sensors = data.get("sensors", {})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    status = evaluasi_kondisi_tanah(
        ph=sensors.get("ph_tanah", 7.0),
        n=sensors.get("nitrogen", 0),
        p=sensors.get("fosfor", 0),
        k=sensors.get("kalium", 0),
    )

    hasil = await generate_saran_tanaman(
        ph          =sensors.get("ph_tanah"),
        nitrogen    =sensors.get("nitrogen"),
        fosfor      =sensors.get("fosfor"),
        kalium      =sensors.get("kalium"),
        suhu_udara  =sensors.get("suhu_udara"),
        status_tanah=status,
    )

    if not hasil["sukses"]:
        status_code = hasil.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=hasil["error"])

    return {
        "sukses": True,
        "kondisi_tanah": {
            "ph_tanah": sensors.get("ph_tanah"),
            "nitrogen": sensors.get("nitrogen"),
            "fosfor":   sensors.get("fosfor"),
            "kalium":   sensors.get("kalium"),
            **status,
        },
        "saran_tanaman": hasil["data"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2B. ALUR 2: SARAN TANAMAN + DOSIS PUPUK SEMUSIM (AUTOMATIC)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/alur2-saran",
    summary="Alur 2: 2-3 Saran Tanaman + Dosis Pupuk Semusim berdasarkan tanah",
)
async def post_alur2_saran(
    request: Alur2SaranTanamanDanPupukRequest,
    db: Session = Depends(get_db)
):
    """
    Rekomendasi End-to-End (Alur 2).
    1. Membaca data tanah aktual.
    2. Menentukan 2-3 tanaman yang paling cocok.
    3. Menghitung otomatis dosis pupuk "Total Semusim" untuk tiap tanaman terpilih.
    4. Menggunakan AI untuk merangkum hasil dan memberikan ringkasan yang mudah dipahami.
    """
    # ── 1. Ambil data sensor
    if request.gunakan_sensor_live:
        try:
            raw_data  = baca_sensor_json()
            sensors   = raw_data.get("sensors", {})
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        if not request.data_sensor:
            raise HTTPException(
                status_code=400,
                detail="data_sensor wajib diisi jika gunakan_sensor_live=False",
            )
        sensors = request.data_sensor.model_dump()

    # ── 2. Panggil AI Service Multi-Step
    hasil_ai = await generate_alur2_saran_tanaman_dan_pupuk(
        db=db,
        luas_lahan=request.luas_lahan,
        ph=sensors.get("ph_tanah", 7.0),
        nitrogen=sensors.get("nitrogen", 0),
        fosfor=sensors.get("fosfor", 0),
        kalium=sensors.get("kalium", 0),
        suhu_udara=sensors.get("suhu_udara"),
        kelembaban_tanah=sensors.get("kelembaban_tanah"),
        catatan_tambahan=request.catatan_tambahan
    )

    if not hasil_ai["sukses"]:
        status_code = hasil_ai.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=hasil_ai["error"])

    # ── 3. Return JSON Terstruktur
    status_tanah = evaluasi_kondisi_tanah(
        ph=sensors.get("ph_tanah", 7.0),
        n=sensors.get("nitrogen", 0),
        p=sensors.get("fosfor", 0),
        k=sensors.get("kalium", 0)
    )

    return {
        "sukses": True,
        "kondisi_tanah": {
            "ph_tanah": sensors.get("ph_tanah"),
            "nitrogen": sensors.get("nitrogen"),
            "fosfor":   sensors.get("fosfor"),
            "kalium":   sensors.get("kalium"),
            **status_tanah,
        },
        "saran_alur2": hasil_ai["data"],
        "dibuat_pada": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. REKOMENDASI PUPUK  (setelah user memilih tanaman - ALUR 1)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/rekomendasi",
    summary="AI: Rekomendasi pupuk spesifik berdasarkan tanaman pilihan + kondisi tanah",
)
async def post_rekomendasi_pupuk(
    request: RekomendasiPupukRequest,
    db:      Session = Depends(get_db),
):
    """
    Generate rekomendasi pupuk untuk tanaman yang dipilih user.

    **Alur lengkap:**
    1. Baca data sensor (dari file JSON / manual)
    2. Evaluasi kondisi tanah (status pH, N, P, K)
    3. Ambil riwayat data lahan untuk konteks pembelajaran AI
    4. Kirim ke Claude API:
       - Data sensor aktual
       - Profil kebutuhan NPK spesifik tanaman pilihan user
       - Riwayat historis lahan (makin banyak data → makin akurat)
    5. Claude menganalisis GAP dan menghasilkan rekomendasi pupuk
    6. Simpan semua data ke MySQL untuk pembelajaran berikutnya

    **Catatan penting:** Rekomendasi untuk PADI berbeda dengan JAGUNG, CABAI, dll.
    karena setiap tanaman punya kebutuhan NPK dan pH yang berbeda.
    """
    # ── 1. Ambil data sensor ─────────────────────────────────────────────────
    if request.gunakan_sensor_live:
        try:
            raw_data  = baca_sensor_json()
            sensors   = raw_data.get("sensors", {})
            device_id = raw_data.get("device_id", "json_statis")
            lokasi    = request.lokasi or raw_data.get("lokasi", "Tidak diketahui")
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        if not request.data_sensor:
            raise HTTPException(
                status_code=400,
                detail="data_sensor wajib diisi jika gunakan_sensor_live=False",
            )
        sensors   = request.data_sensor.model_dump()
        device_id = "manual_input"
        lokasi    = request.lokasi or "Input Manual"
        raw_data  = {"sensors": sensors, "device_id": device_id, "lokasi": lokasi}

    # ── 2. Sesi & evaluasi tanah ─────────────────────────────────────────────
    sesi_id     = get_atau_buat_sesi()
    status_tanah = evaluasi_kondisi_tanah(
        ph=sensors.get("ph_tanah"),
        n =sensors.get("nitrogen"),
        p =sensors.get("fosfor"),
        k =sensors.get("kalium"),
    )

    # ── 3. Simpan log & sesi ke DB ───────────────────────────────────────────
    simpan_sesi(
        db            =db,
        sesi_id       =sesi_id,
        device_id     =device_id,
        lokasi        =lokasi,
        jenis_tanaman =request.jenis_tanaman,
        fase_tumbuh   =request.fase_tumbuh,
        luas_lahan    =request.luas_lahan,
        sensor_data   =raw_data,
    )
    simpan_log_sensor(db, sesi_id, raw_data, device_id)

    # ── 4. Ambil riwayat untuk pembelajaran AI ───────────────────────────────
    riwayat = ambil_riwayat_untuk_pembelajaran(
        db            =db,
        jenis_tanaman =request.jenis_tanaman,
        limit         =8,
    )

    # ── 5. Panggil Claude AI ─────────────────────────────────────────────────
    hasil_ai = await generate_rekomendasi_pupuk(
        db               =db,
        jenis_tanaman    =request.jenis_tanaman,
        fase_tumbuh      =request.fase_tumbuh,
        luas_lahan       =request.luas_lahan,
        ph               =sensors.get("ph_tanah"),
        nitrogen         =sensors.get("nitrogen"),
        fosfor           =sensors.get("fosfor"),
        kalium           =sensors.get("kalium"),
        suhu_udara       =sensors.get("suhu_udara"),
        kelembaban_tanah =sensors.get("kelembaban_tanah"),
        catatan_tambahan =request.catatan_tambahan,
        status_tanah     =status_tanah,
        riwayat_lahan    =riwayat,
    )

    if not hasil_ai["sukses"]:
        status_code = hasil_ai.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=hasil_ai["error"])

    data_ai = hasil_ai["data"]

    # ── 6. Simpan rekomendasi ke DB ──────────────────────────────────────────
    kesesuaian     = data_ai.get("kesesuaian_tanaman", {}).get("skor", "-")
    rekomendasi_id = simpan_rekomendasi_pupuk(
        db                   =db,
        sesi_id              =sesi_id,
        jenis_tanaman        =request.jenis_tanaman,
        kondisi_ringkasan    =data_ai.get("kondisi_ringkasan", ""),
        kesesuaian_tanaman   =kesesuaian,
        hasil_ai             =data_ai,
        estimasi_peningkatan =data_ai.get("estimasi_peningkatan", "-"),
    )

    # ── 7. Response ──────────────────────────────────────────────────────────
    return {
        "sukses":          True,
        "rekomendasi_id":  rekomendasi_id,
        "sesi_id":         sesi_id,
        "jenis_tanaman":   request.jenis_tanaman,
        "fase_tumbuh":     request.fase_tumbuh,
        "luas_lahan":      request.luas_lahan,
        "kondisi_tanah": {
            "ph_tanah": sensors.get("ph_tanah"),
            "nitrogen": sensors.get("nitrogen"),
            "fosfor":   sensors.get("fosfor"),
            "kalium":   sensors.get("kalium"),
            **status_tanah,
        },
        # Validasi: apakah tanaman pilihan cocok dengan kondisi tanah ini?
        "kesesuaian_tanaman":        data_ai.get("kesesuaian_tanaman", {}),
        # Analisis gap: kondisi aktual vs kebutuhan spesifik tanaman
        "analisis_gap":              data_ai.get("analisis_gap", {}),
        "kondisi_ringkasan":         data_ai.get("kondisi_ringkasan"),
        "daftar_pupuk":              data_ai.get("daftar_pupuk", []),
        "jadwal_aplikasi":           data_ai.get("jadwal_aplikasi"),
        "estimasi_peningkatan":      data_ai.get("estimasi_peningkatan"),
        "catatan_penting":           data_ai.get("catatan_penting"),
        "peringatan":                data_ai.get("peringatan", []),
        "pembelajaran_dari_riwayat": data_ai.get("pembelajaran_dari_riwayat", ""),
        "jumlah_riwayat_digunakan":  len(riwayat),
        "dibuat_pada":               datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/feedback",
    summary="Kirim feedback hasil rekomendasi (memperkuat pembelajaran AI)",
)
def post_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Petani atau operator mengirim feedback setelah mengaplikasikan pupuk.
    Rating 1–5 dan catatan hasil disimpan untuk validasi dan perbaikan AI ke depan.
    """
    ok = simpan_feedback(db, request.rekomendasi_id, request.rating, request.catatan_hasil, jenis="pupuk")
    if not ok:
        raise HTTPException(status_code=500, detail="Gagal menyimpan feedback")

    return {
        "sukses":         True,
        "pesan":          "Terima kasih! Feedback Anda membantu AI memberikan rekomendasi lebih baik.",
        "rekomendasi_id": request.rekomendasi_id,
        "rating":         request.rating,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. RESET SESI
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/reset-sesi",
    summary="Reset sesi untuk memulai pengujian tanah baru",
)
def post_reset_sesi(request: ResetSesiRequest, db: Session = Depends(get_db)):
    """
    Reset sesi aktif untuk pengujian tanah baru.

    ⚠️ Data sesi lama **TIDAK dihapus** — tersimpan di database dan akan
    digunakan AI sebagai konteks pembelajaran pada sesi berikutnya.
    Semakin banyak sesi tersimpan, semakin akurat rekomendasi AI.
    """
    sesi_lama = get_atau_buat_sesi()
    tandai_sesi_reset(db, sesi_lama, request.catatan_reset)
    sesi_baru = reset_sesi()

    return {
        "sukses":    True,
        "pesan":     "Sesi berhasil direset. Data lama tersimpan untuk pembelajaran AI.",
        "sesi_lama": sesi_lama,
        "sesi_baru": sesi_baru,
        "lokasi_baru": request.lokasi_baru,
        "waktu_reset": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. DATA, RIWAYAT & STATISTIK
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/riwayat", summary="Riwayat semua rekomendasi")
def get_riwayat(
    limit: int     = Query(20, ge=1, le=100),
    db:    Session = Depends(get_db),
):
    """Riwayat rekomendasi untuk dashboard publik dan bahan pembelajaran AI."""
    data = ambil_riwayat_rekomendasi(db, limit)
    return {"sukses": True, "total": len(data), "data": data}


@router.get("/statistik", summary="Statistik global + tren kondisi tanah")
def get_statistik(db: Session = Depends(get_db)):
    """
    Statistik sistem: total sesi, total rekomendasi, rata-rata kondisi tanah,
    tanaman yang paling banyak dianalisis, dan tren pH 7 hari terakhir.
    """
    return {"sukses": True, "data": ambil_statistik(db)}


@router.get("/sesi/aktif", summary="Info sesi pengujian aktif saat ini")
def get_sesi_aktif():
    return get_info_sesi()


@router.get("/tanaman/daftar", summary="Daftar 60+ tanaman dari Master Data Agronomi")
def get_daftar_tanaman(db: Session = Depends(get_db)):
    """
    Mengambil daftar tanaman dari tabel kebutuhan_hara di database.
    Ini memastikan data yang tampil di frontend sinkron dengan Rule Engine.
    """
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT nama_tanaman, ph_min, ph_max, n_req, p_req, k_req, kebutuhan_air
        FROM kebutuhan_hara
        ORDER BY nama_tanaman ASC
    """)).fetchall()

    return {
        "sukses": True,
        "total": len(rows),
        "tanaman": [
            {
                "nama":          row[0],
                "ph_ideal":      f"{row[1]}–{row[2]}",
                "kebutuhan_n":   "Tinggi" if row[3] > 140 else ("Sedang" if row[3] > 80 else "Rendah"),
                "kebutuhan_p":   "Tinggi" if row[4] > 90 else ("Sedang" if row[4] > 60 else "Rendah"),
                "kebutuhan_k":   "Tinggi" if row[5] > 140 else ("Sedang" if row[5] > 80 else "Rendah"),
                "n_req":         row[3],
                "p_req":         row[4],
                "k_req":         row[5],
                "ph_min":        row[1],
                "ph_max":        row[2],
                "kebutuhan_air": row[6],
            }
            for row in rows
        ],
    }


@router.get("/rekomendasi/{rekomendasi_id}/pdf", summary="Download PDF Rekomendasi Pupuk")
def get_rekomendasi_pdf(rekomendasi_id: int, db: Session = Depends(get_db)):
    data = ambil_rekomendasi_pupuk_by_id(db, rekomendasi_id)
    if not data:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan")

    pdf_bytes = generate_pupuk_pdf(data)
    
    filename = f"Rekomendasi_Pupuk_{data['jenis_tanaman']}_{rekomendasi_id}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/riwayat/export/csv", summary="Export riwayat pupuk ke CSV")
def get_export_pupuk_csv(db: Session = Depends(get_db)):
    """Download semua riwayat rekomendasi pupuk dalam format CSV."""
    from app.services.export_service import export_riwayat_pupuk_csv
    csv_bytes = export_riwayat_pupuk_csv(db)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=riwayat_pupuk_{datetime.now().strftime('%Y%m%d')}.csv"}
    )