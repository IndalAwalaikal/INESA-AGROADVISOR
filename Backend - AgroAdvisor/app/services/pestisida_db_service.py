import json
from sqlalchemy.orm import Session
from sqlalchemy import text


def simpan_rekomendasi_pestisida(
    db:                   Session,
    sesi_id:              str,
    jenis_tanaman:        str,
    jenis_hama:           str,
    tingkat_serangan:     str,
    hasil_ai:             dict,
    estimasi_efektivitas: str,
) -> int:
    """Simpan hasil rekomendasi pestisida beserta detail tiap item. Kembalikan ID."""
    result = db.execute(text("""
        INSERT INTO rekomendasi_pestisida
            (sesi_id, jenis_tanaman, jenis_hama, tingkat_serangan,
             rekomendasi_json, estimasi_efektivitas, catatan_ai)
        VALUES
            (:sesi_id, :tanaman, :hama, :tingkat,
             :json_data, :estimasi, :catatan)
    """), {
        "sesi_id":  sesi_id,
        "tanaman":  jenis_tanaman,
        "hama":     jenis_hama,
        "tingkat":  tingkat_serangan,
        "json_data": json.dumps(hasil_ai, ensure_ascii=False),
        "estimasi": estimasi_efektivitas,
        "catatan":  hasil_ai.get("catatan_keamanan", ""),
    })
    db.commit()
    rekomendasi_id = result.lastrowid

    for item in hasil_ai.get("daftar_pestisida", []):
        db.execute(text("""
            INSERT INTO detail_pestisida
                (rekomendasi_id, sesi_id, nama_pestisida, bahan_aktif,
                 jenis_pestisida, dosis_per_liter, dosis_per_ha,
                 waktu_semprot, interval_semprot, metode_aplikasi,
                 phi, tujuan, urutan)
            VALUES
                (:rek_id, :sesi_id, :nama, :aktif,
                 :jenis, :per_liter, :per_ha,
                 :waktu, :interval, :metode,
                 :phi, :tujuan, :urutan)
        """), {
            "rek_id":    rekomendasi_id,
            "sesi_id":   sesi_id,
            "nama":      item.get("nama_pestisida"),
            "aktif":     item.get("bahan_aktif"),
            "jenis":     item.get("jenis_pestisida"),
            "per_liter": item.get("dosis_per_liter_air"),
            "per_ha":    item.get("dosis_per_ha"),
            "waktu":     item.get("waktu_semprot"),
            "interval":  item.get("interval_semprot"),
            "metode":    item.get("metode_aplikasi"),
            "phi":       item.get("phi"),
            "tujuan":    item.get("tujuan"),
            "urutan":    item.get("urutan", 1),
        })
    db.commit()
    return rekomendasi_id


def ambil_riwayat_untuk_pembelajaran_hama(
    db:            Session,
    jenis_tanaman: str  = None,
    jenis_hama:    str  = None,
    limit:         int  = 8,
) -> list:
    """Riwayat penanganan hama untuk konteks pembelajaran AI."""
    params = {"limit": limit}
    where  = []

    if jenis_tanaman:
        where.append("p.jenis_tanaman = :tanaman")
        params["tanaman"] = jenis_tanaman.lower()
    if jenis_hama:
        where.append("p.jenis_hama LIKE :hama")
        params["hama"] = f"%{jenis_hama}%"

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    rows = db.execute(text(f"""
        SELECT p.jenis_tanaman, p.jenis_hama, p.tingkat_serangan,
               p.estimasi_efektivitas, p.catatan_ai, p.dibuat_pada
        FROM rekomendasi_pestisida p
        {where_clause}
        ORDER BY p.dibuat_pada DESC
        LIMIT :limit
    """), params).fetchall()

    return [
        {
            "jenis_tanaman":    row[0],
            "jenis_hama":       row[1],
            "tingkat_serangan": row[2],
            "ringkasan":        row[4],
            "tanggal":          str(row[5]),
        }
        for row in rows
    ]


def ambil_riwayat_pestisida(db: Session, limit: int = 20) -> list:
    """Riwayat rekomendasi pestisida untuk dashboard publik."""
    rows = db.execute(text("""
        SELECT id, sesi_id, jenis_tanaman, jenis_hama,
               tingkat_serangan, estimasi_efektivitas, dibuat_pada, rekomendasi_json
        FROM rekomendasi_pestisida
        ORDER BY dibuat_pada DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        {
            "id":                   row[0],
            "sesi_id":              row[1],
            "jenis_tanaman":        row[2],
            "jenis_hama":           row[3],
            "tingkat_serangan":     row[4],
            "estimasi_efektivitas": row[5],
            "dibuat_pada":          str(row[6]),
            "rekomendasi_json":     json.loads(row[7]) if row[7] else None,
        }
        for row in rows
    ]


def ambil_rekomendasi_pestisida_by_id(db: Session, rek_id: int) -> dict:
    """Ambil satu baris rekomendasi pestisida berdasarkan ID."""
    row = db.execute(text("""
        SELECT id, sesi_id, jenis_tanaman, jenis_hama,
               tingkat_serangan, estimasi_efektivitas, dibuat_pada, rekomendasi_json
        FROM rekomendasi_pestisida
        WHERE id = :rek_id
    """), {"rek_id": rek_id}).fetchone()

    if not row:
        return None

    res = {
        "id":                   row[0],
        "sesi_id":              row[1],
        "jenis_tanaman":        row[2],
        "jenis_hama":           row[3],
        "tingkat_serangan":     row[4],
        "estimasi_efektivitas": row[5],
        "dibuat_pada":          str(row[6]),
    }

    if row[7]:
        rek_json = json.loads(row[7])
        res.update(rek_json)
        # Pastikan data yang diperlukan pdf_service ada
        if "identifikasi" not in res:
             res["identifikasi"] = {"nama_umum": row[3]}

    return res