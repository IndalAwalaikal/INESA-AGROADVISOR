from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.services.sensor_service import (
    baca_sensor_json,
    get_atau_buat_sesi,
    evaluasi_kondisi_tanah,
)
from app.services.pestisida_ai_service import (
    generate_rekomendasi_pestisida,
    identifikasi_hama_dari_gambar,
    get_profil_hama,
    PROFIL_HAMA,
)
from app.services.pestisida_db_service import (
    ambil_riwayat_untuk_pembelajaran_hama,
    ambil_riwayat_pestisida,
    ambil_rekomendasi_pestisida_by_id,
    simpan_rekomendasi_pestisida,
)
from app.services.pdf_service import generate_pestisida_pdf
from fastapi.responses import Response
from app.services.db_service import simpan_log_sensor, simpan_feedback
from app.models.schemas import FeedbackRequest

router = APIRouter(prefix="/api/pestisida", tags=["Rekomendasi Pestisida"])


# ─── Request Models ───────────────────────────────────────────────────────────

class RekomendasiPestisidaRequest(BaseModel):
    jenis_tanaman:      str           = Field(..., description="Contoh: padi, jagung, cabai")
    jenis_hama:         str           = Field(..., description="Contoh: wereng coklat, ulat grayak, antraknosa")
    tingkat_serangan:   str           = Field("sedang", description="ringan | sedang | berat")
    luas_lahan:         float         = Field(1.0, ge=0.01, description="Luas lahan dalam hektar")
    usia_tanaman:       Optional[str] = Field(None, description="Contoh: 45 HST, 3 bulan")
    riwayat_pestisida:  Optional[str] = Field(None, description="Pestisida yang pernah dipakai sebelumnya")
    catatan_tambahan:   Optional[str] = None
    gunakan_sensor_live: bool         = Field(True, description="Ambil data cuaca dari sensor IoT")


# ─────────────────────────────────────────────────────────────────────────────
# 1. REKOMENDASI PESTISIDA
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/rekomendasi",
    summary="AI: Rekomendasi pestisida berdasarkan jenis hama + tanaman",
)
async def post_rekomendasi_pestisida(
    request: RekomendasiPestisidaRequest,
    db:      Session = Depends(get_db),
):
    """
    Generate rekomendasi pestisida yang tepat untuk hama/penyakit pada tanaman pilihan.

    **Alur:**
    1. Baca kondisi cuaca dari sensor (suhu, hujan) untuk penyesuaian jadwal semprot
    2. Ambil riwayat penanganan hama yang sama untuk konteks pembelajaran AI
    3. AI analisis jenis hama, tingkat serangan, dan kondisi aktual
    4. Kembalikan rekomendasi: nama pestisida, dosis, waktu semprot, interval, PHI
    5. Simpan ke database untuk pembelajaran berikutnya

    **Catatan:** Rekomendasi mengikuti prinsip PHT (Pengendalian Hama Terpadu)
    dan selalu menyertakan PHI (Pre-Harvest Interval) demi keamanan pangan.
    """
    # 1. Ambil data sensor untuk kondisi cuaca
    suhu_udara       = None
    hujan_terdeteksi = False
    sesi_id          = get_atau_buat_sesi()

    if request.gunakan_sensor_live:
        try:
            raw_data         = baca_sensor_json()
            sensors          = raw_data.get("sensors", {})
            suhu_udara       = sensors.get("suhu_udara")
            hujan_terdeteksi = sensors.get("hujan_terdeteksi", False)
            simpan_log_sensor(db, sesi_id, raw_data, raw_data.get("device_id"))
        except FileNotFoundError:
            pass  # Lanjut tanpa data sensor

    # 2. Ambil riwayat untuk pembelajaran AI
    riwayat = ambil_riwayat_untuk_pembelajaran_hama(
        db            =db,
        jenis_tanaman =request.jenis_tanaman,
        jenis_hama    =request.jenis_hama,
        limit         =6,
    )

    # 3. Panggil Claude AI
    hasil_ai = await generate_rekomendasi_pestisida(
        db                =db,
        jenis_tanaman     =request.jenis_tanaman,
        jenis_hama        =request.jenis_hama,
        tingkat_serangan  =request.tingkat_serangan,
        luas_lahan        =request.luas_lahan,
        usia_tanaman      =request.usia_tanaman,
        riwayat_pestisida =request.riwayat_pestisida,
        catatan_tambahan  =request.catatan_tambahan,
        suhu_udara        =suhu_udara,
        hujan_terdeteksi  =hujan_terdeteksi,
        riwayat_lahan     =riwayat,
    )

    if not hasil_ai["sukses"]:
        status_code = hasil_ai.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=hasil_ai["error"])

    data_ai = hasil_ai["data"]

    # 4. Simpan ke DB
    rekomendasi_id = simpan_rekomendasi_pestisida(
        db                   =db,
        sesi_id              =sesi_id,
        jenis_tanaman        =request.jenis_tanaman,
        jenis_hama           =request.jenis_hama,
        tingkat_serangan     =request.tingkat_serangan,
        hasil_ai             =data_ai,
        estimasi_efektivitas =data_ai.get("estimasi_efektivitas", "-"),
    )

    return {
        "sukses":          True,
        "rekomendasi_id":  rekomendasi_id,
        "sesi_id":         sesi_id,
        "jenis_tanaman":   request.jenis_tanaman,
        "jenis_hama":      request.jenis_hama,
        "tingkat_serangan": request.tingkat_serangan,
        "luas_lahan":      request.luas_lahan,
        "kondisi_cuaca": {
            "suhu_udara":       suhu_udara,
            "hujan_terdeteksi": hujan_terdeteksi,
        },
        "identifikasi":            data_ai.get("identifikasi", {}),
        "strategi_pengendalian":   data_ai.get("strategi_pengendalian"),
        "daftar_pestisida":        data_ai.get("daftar_pestisida", []),
        "kombinasi_diizinkan":     data_ai.get("kombinasi_diizinkan", []),
        "kombinasi_dilarang":      data_ai.get("kombinasi_dilarang", []),
        "alternatif_organik":      data_ai.get("alternatif_organik", []),
        "jadwal_pengendalian":     data_ai.get("jadwal_pengendalian"),
        "estimasi_efektivitas":    data_ai.get("estimasi_efektivitas"),
        "tanda_berhasil":          data_ai.get("tanda_berhasil"),
        "catatan_keamanan":        data_ai.get("catatan_keamanan"),
        "peringatan":              data_ai.get("peringatan", []),
        "jumlah_riwayat_digunakan": len(riwayat),
        "dibuat_pada":             datetime.now().isoformat(),
    }


@router.post(
    "/identifikasi-gambar",
    summary="AI: Identifikasi hama tanaman dari foto/gambar",
)
async def post_identifikasi_gambar(
    file: UploadFile = File(...)
):
    """
    Identifikasi jenis hama atau penyakit dari gambar yang diupload.
    Hanya menerima format gambar (JPEG, PNG). Maksimal 10MB (disarankan).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar (JPG/PNG)")
        
    try:
        # Baca bytes dari gambar
        image_bytes = await file.read()
        
        # Panggil AI Vision
        hasil_ai = await identifikasi_hama_dari_gambar(
            image_bytes=image_bytes, 
            mime_type=file.content_type
        )
        
        if not hasil_ai["sukses"]:
            raise HTTPException(status_code=500, detail=hasil_ai["error"])
            
        return {
            "sukses": True,
            "nama_hama": hasil_ai.get("nama_hama"),
            "pesan": "Berhasil mengidentifikasi gambar"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan saat memproses gambar: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA REFERENSI
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/hama/daftar",
    summary="Daftar hama & penyakit umum per tanaman",
)
def get_daftar_hama(tanaman: Optional[str] = Query(None, description="Filter per tanaman")):
    """
    Daftar hama dan penyakit umum yang didukung sistem.
    Frontend dapat menggunakan ini untuk autocomplete saat user input jenis hama.
    """
    if tanaman:
        kunci = tanaman.lower().strip()
        if kunci not in PROFIL_HAMA:
            raise HTTPException(status_code=404, detail=f"Tanaman '{tanaman}' tidak ada dalam daftar")
        return {
            "sukses":  True,
            "tanaman": tanaman,
            "data":    PROFIL_HAMA[kunci],
        }

    return {
        "sukses": True,
        "total":  len(PROFIL_HAMA),
        "data": {
            nama: {
                "hama_umum":     profil["hama_umum"],
                "penyakit_umum": profil["penyakit_umum"],
            }
            for nama, profil in PROFIL_HAMA.items()
        },
    }


@router.get("/riwayat", summary="Riwayat rekomendasi pestisida")
def get_riwayat_pestisida(
    limit: int     = Query(20, ge=1, le=100),
    db:    Session = Depends(get_db),
):
    data = ambil_riwayat_pestisida(db, limit)
    return {"sukses": True, "total": len(data), "data": data}


@router.post(
    "/feedback",
    summary="Kirim feedback hasil rekomendasi pestisida",
)
def post_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Simpan feedback rating dan catatan hasil penanganan hama.
    """
    ok = simpan_feedback(db, request.rekomendasi_id, request.rating, request.catatan_hasil, jenis="pestisida")
    if not ok:
        raise HTTPException(status_code=500, detail="Gagal menyimpan feedback")

    return {
        "sukses":         True,
        "pesan":          "Terima kasih atas feedback Anda!",
        "rekomendasi_id": request.rekomendasi_id,
    }


@router.get("/rekomendasi/{rekomendasi_id}/pdf", summary="Download PDF Rekomendasi Pestisida")
def get_rekomendasi_pestisida_pdf(rekomendasi_id: int, db: Session = Depends(get_db)):
    data = ambil_rekomendasi_pestisida_by_id(db, rekomendasi_id)
    if not data:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan")

    pdf_bytes = generate_pestisida_pdf(data)
    
    filename = f"Rekomendasi_Pestisida_{data['jenis_hama']}_{rekomendasi_id}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/riwayat/export/csv", summary="Export riwayat pestisida ke CSV")
def get_export_pestisida_csv(db: Session = Depends(get_db)):
    """Download semua riwayat rekomendasi pestisida dalam format CSV."""
    from app.services.export_service import export_riwayat_pestisida_csv
    csv_bytes = export_riwayat_pestisida_csv(db)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=riwayat_pestisida_{datetime.now().strftime('%Y%m%d')}.csv"}
    )