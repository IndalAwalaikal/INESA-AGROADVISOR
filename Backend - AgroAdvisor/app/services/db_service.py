import json
from sqlalchemy.orm import Session
from sqlalchemy import text


# ─── Sesi Pengujian ───────────────────────────────────────────────────────────

def simpan_sesi(
    db:            Session,
    sesi_id:       str,
    device_id:     str,
    lokasi:        str,
    jenis_tanaman: str,
    fase_tumbuh:   str,
    luas_lahan:    float,
    sensor_data:   dict,
):
    """Simpan sesi pengujian baru jika belum ada."""
    ada = db.execute(
        text("SELECT id FROM sesi_pengujian WHERE sesi_id = :sid"),
        {"sid": sesi_id},
    ).fetchone()

    if ada:
        return  # Sudah ada, skip

    s = sensor_data.get("sensors", sensor_data)
    db.execute(text("""
        INSERT INTO sesi_pengujian (
            sesi_id, device_id, lokasi, jenis_tanaman, fase_tumbuh, luas_lahan,
            ph_tanah, nitrogen, fosfor, kalium,
            suhu_udara, kelembaban_udara, kelembaban_tanah, hujan_terdeteksi
        ) VALUES (
            :sesi_id, :device_id, :lokasi, :jenis_tanaman, :fase_tumbuh, :luas_lahan,
            :ph, :n, :p, :k, :suhu, :hum_udara, :hum_tanah, :hujan
        )
    """), {
        "sesi_id":      sesi_id,
        "device_id":    device_id,
        "lokasi":       lokasi,
        "jenis_tanaman": jenis_tanaman,
        "fase_tumbuh":  fase_tumbuh,
        "luas_lahan":   luas_lahan,
        "ph":           s.get("ph_tanah"),
        "n":            s.get("nitrogen"),
        "p":            s.get("fosfor"),
        "k":            s.get("kalium"),
        "suhu":         s.get("suhu_udara"),
        "hum_udara":    s.get("kelembaban_udara"),
        "hum_tanah":    s.get("kelembaban_tanah"),
        "hujan":        s.get("hujan_terdeteksi", False),
    })
    db.commit()


def tandai_sesi_reset(db: Session, sesi_id: str, catatan: str = None):
    """Tandai sesi sebagai selesai saat di-reset. Data tetap ada."""
    db.execute(text("""
        UPDATE sesi_pengujian
        SET status = 'selesai', direset_pada = NOW(), catatan = :catatan
        WHERE sesi_id = :sesi_id
    """), {"sesi_id": sesi_id, "catatan": catatan or "Reset oleh operator"})
    db.commit()


# ─── Log Sensor ───────────────────────────────────────────────────────────────

def simpan_log_sensor(db: Session, sesi_id: str, sensor_data: dict, device_id: str = None):
    """
    Catat setiap pembacaan sensor ke tabel log.
    Data ini digunakan sebagai bahan pembelajaran AI.
    """
    s = sensor_data.get("sensors", sensor_data)
    db.execute(text("""
        INSERT INTO log_sensor (
            sesi_id, device_id, ph_tanah, nitrogen, fosfor, kalium,
            suhu_udara, kelembaban_udara, kelembaban_tanah, hujan_terdeteksi
        ) VALUES (
            :sesi_id, :device_id, :ph, :n, :p, :k,
            :suhu, :hum_udara, :hum_tanah, :hujan
        )
    """), {
        "sesi_id":   sesi_id,
        "device_id": device_id or "unknown",
        "ph":        s.get("ph_tanah"),
        "n":         s.get("nitrogen"),
        "p":         s.get("fosfor"),
        "k":         s.get("kalium"),
        "suhu":      s.get("suhu_udara"),
        "hum_udara": s.get("kelembaban_udara"),
        "hum_tanah": s.get("kelembaban_tanah"),
        "hujan":     s.get("hujan_terdeteksi", False),
    })
    db.commit()


# ─── Rekomendasi Pupuk ────────────────────────────────────────────────────────

def simpan_rekomendasi_pupuk(
    db:                   Session,
    sesi_id:              str,
    jenis_tanaman:        str,
    kondisi_ringkasan:    str,
    kesesuaian_tanaman:   str,
    hasil_ai:             dict,
    estimasi_peningkatan: str,
) -> int:
    """Simpan hasil rekomendasi AI beserta detail tiap pupuk. Kembalikan ID."""
    result = db.execute(text("""
        INSERT INTO rekomendasi_pupuk (
            sesi_id, jenis_tanaman, kondisi_tanah_ringkasan,
            kesesuaian_tanaman, rekomendasi_json, estimasi_peningkatan, catatan_ai
        ) VALUES (
            :sesi_id, :tanaman, :ringkasan,
            :kesesuaian, :json_data, :estimasi, :catatan
        )
    """), {
        "sesi_id":    sesi_id,
        "tanaman":    jenis_tanaman,
        "ringkasan":  kondisi_ringkasan,
        "kesesuaian": kesesuaian_tanaman,
        "json_data":  json.dumps(hasil_ai, ensure_ascii=False),
        "estimasi":   estimasi_peningkatan,
        "catatan":    hasil_ai.get("catatan_penting", ""),
    })
    db.commit()
    rekomendasi_id = result.lastrowid

    # Simpan detail tiap item pupuk
    for item in hasil_ai.get("daftar_pupuk", []):
        db.execute(text("""
            INSERT INTO detail_pupuk (
                rekomendasi_id, sesi_id, nama_pupuk, bahan_aktif,
                takaran_per_ha, takaran_total, waktu_aplikasi,
                metode_aplikasi, tujuan, urutan
            ) VALUES (
                :rek_id, :sesi_id, :nama, :aktif,
                :per_ha, :total, :waktu, :metode, :tujuan, :urutan
            )
        """), {
            "rek_id":  rekomendasi_id,
            "sesi_id": sesi_id,
            "nama":    item.get("nama_pupuk"),
            "aktif":   item.get("bahan_aktif"),
            "per_ha":  item.get("takaran_per_ha"),
            "total":   item.get("takaran_total"),
            "waktu":   item.get("waktu_aplikasi"),
            "metode":  item.get("metode_aplikasi"),
            "tujuan":  item.get("tujuan"),
            "urutan":  item.get("urutan", 1),
        })
    db.commit()
    return rekomendasi_id


# ─── Pembelajaran AI ──────────────────────────────────────────────────────────

def ambil_riwayat_untuk_pembelajaran(
    db:            Session,
    jenis_tanaman: str  = None,
    limit:         int  = 10,
) -> list:
    """
    Ambil riwayat data lahan + rekomendasi untuk dijadikan konteks AI.
    Jika jenis_tanaman diisi, prioritaskan riwayat tanaman yang sama.
    Makin banyak data tersimpan → makin akurat rekomendasi AI.
    """
    params = {"limit": limit}

    if jenis_tanaman:
        sql = """
            SELECT r.jenis_tanaman,
                   s.ph_tanah, s.nitrogen, s.fosfor, s.kalium,
                   r.kondisi_tanah_ringkasan,
                   r.estimasi_peningkatan,
                   r.dibuat_pada
            FROM rekomendasi_pupuk r
            JOIN sesi_pengujian s ON r.sesi_id = s.sesi_id
            WHERE r.jenis_tanaman = :tanaman
            ORDER BY r.dibuat_pada DESC
            LIMIT :limit
        """
        params["tanaman"] = jenis_tanaman.lower()
    else:
        sql = """
            SELECT r.jenis_tanaman,
                   s.ph_tanah, s.nitrogen, s.fosfor, s.kalium,
                   r.kondisi_tanah_ringkasan,
                   r.estimasi_peningkatan,
                   r.dibuat_pada
            FROM rekomendasi_pupuk r
            JOIN sesi_pengujian s ON r.sesi_id = s.sesi_id
            ORDER BY r.dibuat_pada DESC
            LIMIT :limit
        """

    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "jenis_tanaman":      row[0],
            "ph_tanah":           row[1],
            "nitrogen":           row[2],
            "fosfor":             row[3],
            "kalium":             row[4],
            "rekomendasi_ringkas": row[5],
            "estimasi":           row[6],
            "tanggal":            str(row[7]),
        }
        for row in rows
    ]


# ─── Feedback ─────────────────────────────────────────────────────────────────

def simpan_feedback(
    db:             Session,
    rekomendasi_id: int,
    rating:         int,
    catatan_hasil:  str = None,
    jenis:          str = "pupuk",
) -> bool:
    """
    Simpan feedback petani (rating 1–5) terhadap rekomendasi.
    Data ini memperkuat validasi kualitas rekomendasi AI di masa depan.
    """
    try:
        db.execute(text("""
            INSERT INTO feedback_rekomendasi (rekomendasi_id, jenis_rekomendasi, rating, catatan_hasil)
            VALUES (:rek_id, :jenis, :rating, :catatan)
        """), {
            "rek_id":  rekomendasi_id,
            "jenis":   jenis,
            "rating":  max(1, min(5, rating)),
            "catatan": catatan_hasil,
        })
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


# ─── Dashboard & Statistik ────────────────────────────────────────────────────

def ambil_riwayat_rekomendasi(db: Session, limit: int = 20) -> list:
    """Riwayat rekomendasi untuk dashboard publik."""
    rows = db.execute(text("""
        SELECT r.id, r.sesi_id, r.jenis_tanaman,
               r.kondisi_tanah_ringkasan, r.kesesuaian_tanaman,
               r.estimasi_peningkatan, r.dibuat_pada, r.rekomendasi_json
        FROM rekomendasi_pupuk r
        ORDER BY r.dibuat_pada DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        {
            "id":                      row[0],
            "sesi_id":                 row[1],
            "jenis_tanaman":           row[2],
            "kondisi_tanah_ringkasan": row[3],
            "kesesuaian_tanaman":      row[4],
            "estimasi_peningkatan":    row[5],
            "dibuat_pada":             str(row[6]),
            "rekomendasi_json":        json.loads(row[7]) if row[7] else None,
        }
        for row in rows
    ]


def ambil_rekomendasi_pupuk_by_id(db: Session, rek_id: int) -> dict:
    """Ambil satu baris rekomendasi pupuk berdasarkan ID."""
    row = db.execute(text("""
        SELECT r.id, r.sesi_id, r.jenis_tanaman,
               r.kondisi_tanah_ringkasan, r.kesesuaian_tanaman,
               r.estimasi_peningkatan, r.dibuat_pada, r.rekomendasi_json,
               s. ph_tanah, s.nitrogen, s.fosfor, s.kalium,
               r.catatan_ai, s.fase_tumbuh, s.luas_lahan
        FROM rekomendasi_pupuk r
        JOIN sesi_pengujian s ON r.sesi_id = s.sesi_id
        WHERE r.id = :rek_id
    """), {"rek_id": rek_id}).fetchone()

    if not row:
        return None

    res = {
        "id":                      row[0],
        "sesi_id":                 row[1],
        "jenis_tanaman":           row[2],
        "kondisi_ringkasan":       row[3],
        "kesesuaian_tanaman":      {"skor": row[4], "saran": ""}, # Simplifikasi untuk PDF
        "estimasi_peningkatan":    row[5],
        "dibuat_pada":             str(row[6]),
        "catatan_penting":         row[12],
        "fase_tumbuh":             row[13],
        "luas_lahan":              row[14],
        "kondisi_tanah": {
            "ph_tanah": row[8],
            "nitrogen": row[9],
            "fosfor":   row[10],
            "kalium":   row[11],
        }
    }

    # Ambil detail dari JSON jika ada
    if row[7]:
        rek_json = json.loads(row[7])
        res["daftar_pupuk"] = rek_json.get("daftar_pupuk", [])
        res["jadwal_aplikasi"] = rek_json.get("jadwal_aplikasi", "")
        if "kesesuaian_tanaman" in rek_json:
             res["kesesuaian_tanaman"] = rek_json["kesesuaian_tanaman"]

    return res


def ambil_statistik(db: Session) -> dict:
    """Statistik global untuk dashboard publik."""
    total_sesi        = db.execute(text("SELECT COUNT(*) FROM sesi_pengujian")).scalar()
    total_rekomendasi = db.execute(text("SELECT COUNT(*) FROM rekomendasi_pupuk")).scalar()
    total_log         = db.execute(text("SELECT COUNT(*) FROM log_sensor")).scalar()

    tanaman_terbanyak = db.execute(text("""
        SELECT jenis_tanaman, COUNT(*) jumlah
        FROM rekomendasi_pupuk
        GROUP BY jenis_tanaman
        ORDER BY jumlah DESC
        LIMIT 5
    """)).fetchall()

    avg_sensor = db.execute(text("""
        SELECT ROUND(AVG(ph_tanah),2), ROUND(AVG(nitrogen),1),
               ROUND(AVG(fosfor),1),  ROUND(AVG(kalium),1)
        FROM log_sensor
    """)).fetchone()

    tren_ph = db.execute(text("""
        SELECT DATE(dicatat_pada) tgl, ROUND(AVG(ph_tanah),2) avg_ph
        FROM log_sensor
        WHERE dicatat_pada >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(dicatat_pada)
        ORDER BY tgl ASC
    """)).fetchall()

    # Hitung total siram hari ini (dari log pompa)
    siram_hari_ini = db.execute(text("""
        SELECT COUNT(*), COALESCE(SUM(durasi_menit), 0)
        FROM log_pompa
        WHERE DATE(dicatat_pada) = CURRENT_DATE()
          AND status IN ('nyala', 'manual_nyala')
    """)).fetchone()

    total_siram = siram_hari_ini[0] if siram_hari_ini else 0
    total_durasi_menit = siram_hari_ini[1] if siram_hari_ini else 0
    # Asumsi kasar pompa: 15 liter per menit
    estimasi_air_liter = total_durasi_menit * 15

    return {
        "total_sesi":        total_sesi,
        "total_rekomendasi": total_rekomendasi,
        "total_log_sensor":  total_log,
        "tanaman_terbanyak": [{"tanaman": r[0], "jumlah": r[1]} for r in tanaman_terbanyak],
        "rata_rata_kondisi_tanah": {
            "ph":       avg_sensor[0] if avg_sensor else None,
            "nitrogen": avg_sensor[1] if avg_sensor else None,
            "fosfor":   avg_sensor[2] if avg_sensor else None,
            "kalium":   avg_sensor[3] if avg_sensor else None,
        },
        "tren_ph_7_hari": [{"tanggal": str(r[0]), "ph": r[1]} for r in tren_ph],
        "total_siram": total_siram,
        "estimasi_air_liter": estimasi_air_liter,
    }
# ─── Master Data: Kebutuhan Hara ──────────────────────────────────────────────

def get_kebutuhan_hara(db: Session, nama_tanaman: str) -> dict:
    """Ambil data kebutuhan hara tanaman dari database."""
    # Cari yang paling mirip atau mengandung nama tersebut
    row = db.execute(text("""
        SELECT nama_tanaman, n_req, p_req, k_req, ph_min, ph_max, kebutuhan_air
        FROM kebutuhan_hara
        WHERE LOWER(nama_tanaman) LIKE :nama
        ORDER BY LENGTH(nama_tanaman) ASC
        LIMIT 1
    """), {"nama": f"%{nama_tanaman.lower()}%"}).fetchone()

    if not row:
        return None

    return {
        "nama":          row[0],
        "n_req":         row[1],
        "p_req":         row[2],
        "k_req":         row[3],
        "ph_min":        row[4],
        "ph_max":        row[5],
        "kebutuhan_air": row[6]
    }

def get_hama_penyakit(db: Session, nama_tanaman: str) -> list:
    """Ambil data hama dan penyakit untuk tanaman tertentu dari database."""
    rows = db.execute(text("""
        SELECT kategori, nama_umum, nama_ilmiah, gejala_utama, saran_produk
        FROM master_hama_penyakit
        WHERE LOWER(nama_tanaman) LIKE :nama
    """), {"nama": f"%{nama_tanaman.lower()}%"}).fetchall()

    return [
        {
            "kategori":     row[0],
            "nama_umum":    row[1],
            "nama_ilmiah":  row[2],
            "gejala_utama": row[3],
            "saran_produk": row[4]
        }
        for row in rows
    ]
