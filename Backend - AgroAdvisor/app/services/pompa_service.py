"""
Pompa Service — Rule Engine Kontrol Pompa Otomatis

Logika:
- Sensor suhu & kelembaban dibaca dari IoT (sementara dari JSON)
- Rule engine evaluasi kondisi setiap siklus
- Jika kondisi memenuhi threshold → kirim perintah ke relay ESP32 (via MQTT nanti)
- Semua keputusan dicatat di log_pompa untuk riwayat & audit
"""
from datetime import datetime, time as dtime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

def _to_time(val):
    if isinstance(val, timedelta):
        total_seconds = int(val.total_seconds())
        h = (total_seconds // 3600) % 24
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return dtime(h, m, s)
    return val



# ─── State Pompa (in-memory, akan diganti Redis saat IoT tersambung) ──────────
_state_pompa = {
    "status":            "mati",        # mati | nyala | manual_nyala | manual_mati
    "nyala_sejak":       None,          # datetime saat pompa dinyalakan
    "mati_sejak":        None,          # datetime saat pompa dimatikan
    "alasan_terakhir":   "",
    "panas_sejak":       None,          # datetime saat suhu mulai > threshold
    "override_manual":   False,         # True = operator ambil alih
    "prediksi_hujan_sejak": None,      # datetime saat prediksi hujan mulai aktif
}


# ─── Ambil Konfigurasi dari DB ────────────────────────────────────────────────

def get_konfigurasi(db: Session) -> dict:
    """Ambil konfigurasi threshold pompa dari database."""
    row = db.execute(text("""
        SELECT suhu_nyala, durasi_panas_menit, kelembaban_nyala, kelembaban_mati,
               maks_durasi_menit, jeda_setelah_menit,
               aktif_jam_mulai, aktif_jam_selesai, mode
        FROM konfigurasi_pompa WHERE id = 1
    """)).fetchone()

    if not row:
        # Kembalikan default jika tabel kosong
        return {
            "suhu_nyala":         33.0,
            "durasi_panas_menit": 120,
            "kelembaban_nyala":   40.0,
            "kelembaban_mati":    60.0,
            "maks_durasi_menit":  45,
            "jeda_setelah_menit": 15,
            "aktif_jam_mulai":    dtime(5, 0),
            "aktif_jam_selesai":  dtime(17, 0),
            "mode":               "otomatis",
        }

    return {
        "suhu_nyala":         row[0],
        "durasi_panas_menit": row[1],
        "kelembaban_nyala":   row[2],
        "kelembaban_mati":    row[3],
        "maks_durasi_menit":  row[4],
        "jeda_setelah_menit": row[5],
        "aktif_jam_mulai":    _to_time(row[6]),
        "aktif_jam_selesai":  _to_time(row[7]),
        "mode":               row[8],
    }


def update_konfigurasi(db: Session, data: dict) -> bool:
    """Update konfigurasi threshold pompa."""
    fields = []
    params = {}
    allowed = [
        "suhu_nyala", "durasi_panas_menit", "kelembaban_nyala", "kelembaban_mati",
        "maks_durasi_menit", "jeda_setelah_menit",
        "aktif_jam_mulai", "aktif_jam_selesai", "mode",
    ]
    for k, v in data.items():
        if k in allowed and v is not None:
            fields.append(f"{k} = :{k}")
            params[k] = v

    if not fields:
        return False

    db.execute(text(f"UPDATE konfigurasi_pompa SET {', '.join(fields)} WHERE id = 1"), params)
    db.commit()

    # Reset override manual jika mode diubah ke otomatis
    if data.get("mode") == "otomatis":
        _state_pompa["override_manual"] = False
        _state_pompa["alasan_terakhir"] = "Dikembalikan ke mode otomatis via pengaturan"

    return True


# ─── Catat Log Pompa ──────────────────────────────────────────────────────────

def catat_log_pompa(
    db:              Session,
    sesi_id:         str,
    status:          str,
    trigger_oleh:    str,
    alasan:          str,
    suhu:            float = None,
    kelembaban:      float = None,
    durasi_menit:    int   = 0,
):
    db.execute(text("""
        INSERT INTO log_pompa
            (sesi_id, status, trigger_oleh, alasan, suhu_saat_itu, kelembaban_saat_itu, durasi_menit)
        VALUES
            (:sesi_id, :status, :trigger, :alasan, :suhu, :kelembaban, :durasi)
    """), {
        "sesi_id":    sesi_id,
        "status":     status,
        "trigger":    trigger_oleh,
        "alasan":     alasan,
        "suhu":       suhu,
        "kelembaban": kelembaban,
        "durasi":     durasi_menit,
    })
    db.commit()


# ─── Rule Engine Utama ────────────────────────────────────────────────────────

def evaluasi_pompa(
    db:              Session,
    sesi_id:         str,
    suhu_udara:      float,
    kelembaban_tanah: float,
    hujan_terdeteksi: bool,
) -> dict:
    """
    Evaluasi kondisi sensor dan putuskan aksi pompa.

    Rules (urutan prioritas):
    1. Jika mode = manual → tidak ada perubahan otomatis
    2. Jika mode = nonaktif → pompa selalu mati
    3. Jika hujan terdeteksi → matikan pompa (jika sedang nyala)
    4. Jika di luar jam aktif → matikan pompa
    5. Jika pompa sedang nyala dan sudah melebihi maks_durasi → matikan
    6. Jika pompa sedang nyala dan kelembaban > kelembaban_mati → matikan (Histeresis)
    7. Jika pompa baru mati dan masih dalam periode jeda → skip
    8. Jika kelembaban tanah < threshold → nyalakan pompa
    9. Jika suhu > threshold selama durasi_panas_menit → nyalakan pompa
    """
    cfg  = get_konfigurasi(db)
    now  = datetime.now()
    aksi = "tidak_ada"
    alasan = ""

    # Rule 1 — mode manual, AI tidak ikut campur
    if cfg["mode"] == "manual" or _state_pompa["override_manual"]:
        return _response_state("manual", "Mode manual aktif — operator yang mengontrol")

    # Rule 1b — mode terjadwal, scheduler yang kontrol
    if cfg["mode"] == "terjadwal":
        from app.services.jadwal_service import get_jadwal_state
        state = get_jadwal_state()
        if state["sedang_berjalan"]:
            return _response_state("nyala", "Pompa terjadwal sedang berjalan")
        return _response_state(_state_pompa["status"], "Mode terjadwal aktif — pompa dikendalikan jadwal")

    # Rule 2 — mode nonaktif
    if cfg["mode"] == "nonaktif":
        if _state_pompa["status"] == "nyala":
            _set_state("mati", "Pompa dimatikan karena mode nonaktif")
            catat_log_pompa(db, sesi_id, "mati", "otomatis", "Mode diset nonaktif", suhu_udara, kelembaban_tanah)
        return _response_state("nonaktif", "Mode pompa dinonaktifkan")

    # Rule 3 — hujan terdeteksi
    if hujan_terdeteksi:
        if _state_pompa["status"] == "nyala":
            durasi = _hitung_durasi_menit(_state_pompa["nyala_sejak"])
            _set_state("mati", "Hujan terdeteksi")
            catat_log_pompa(db, sesi_id, "mati", "otomatis", "Hujan terdeteksi — pompa dimatikan", suhu_udara, kelembaban_tanah, durasi)
            aksi   = "dimatikan"
            alasan = "Hujan terdeteksi — tidak perlu irigasi"
        else:
            alasan = "Hujan terdeteksi — pompa tetap mati"
        return _response_state(_state_pompa["status"], alasan, aksi)

    # Rule 3.5 — cek prakiraan cuaca (jika tersedia)
    try:
        from app.services.weather_service import _cache, cek_hujan_akan_datang
        data_cuaca = _cache.get("data")
        if data_cuaca:
            alert = cek_hujan_akan_datang(data_cuaca, jam_ke_depan=2)
            if alert.get("akan_hujan") and _state_pompa["status"] != "nyala":
                # Lacak kapan prediksi hujan terdekat pertama kali muncul
                if _state_pompa.get("prediksi_hujan_sejak") is None:
                    _state_pompa["prediksi_hujan_sejak"] = now
                
                # Cek batas tunggu (timeout 60 menit)
                durasi_tunggu = int((now - _state_pompa["prediksi_hujan_sejak"]).total_seconds() / 60)
                if durasi_tunggu >= 60:
                    # Sudah menunggu 1 jam tapi sensor tetap mendeteksi kering
                    alasan = f"Prediksi hujan diabaikan (sudah menunggu {durasi_tunggu} menit tapi tetap kering) — lanjut ke evaluasi sensor"
                    # Lanjut ke rule berikutnya (tanah kering/suhu panas)
                else:
                    menit = alert.get("menit_hingga_hujan", 0)
                    alasan = f"Hujan diprediksi dlm ~{menit} mnt (menunggu {durasi_tunggu}/60 mnt) — pompa ditunda"
                    return _response_state("mati", alasan)
            else:
                # Reset jika tidak ada prediksi hujan segera
                _state_pompa["prediksi_hujan_sejak"] = None
    except Exception:
        pass  # Jika weather service error, lanjut ke rule berikutnya

    # Rule 4 — di luar jam operasional
    jam_sekarang = now.time()
    jam_mulai    = cfg["aktif_jam_mulai"]
    jam_selesai  = cfg["aktif_jam_selesai"]
    if not (jam_mulai <= jam_sekarang <= jam_selesai):
        if _state_pompa["status"] == "nyala":
            durasi = _hitung_durasi_menit(_state_pompa["nyala_sejak"])
            _set_state("mati", "Di luar jam operasional")
            catat_log_pompa(db, sesi_id, "mati", "otomatis", "Di luar jam operasional pompa", suhu_udara, kelembaban_tanah, durasi)
            aksi   = "dimatikan"
            alasan = f"Di luar jam operasional ({jam_mulai}–{jam_selesai})"
        else:
            alasan = f"Di luar jam operasional pompa ({jam_mulai}–{jam_selesai})"
        return _response_state(_state_pompa["status"], alasan, aksi)

    # Rule 5 — pompa sedang nyala, cek maks durasi
    if _state_pompa["status"] == "nyala":
        durasi_nyala = _hitung_durasi_menit(_state_pompa["nyala_sejak"])
        if durasi_nyala >= cfg["maks_durasi_menit"]:
            _set_state("mati", f"Maks durasi {cfg['maks_durasi_menit']} menit tercapai")
            catat_log_pompa(db, sesi_id, "mati", "otomatis",
                f"Pompa dimatikan otomatis setelah {durasi_nyala} menit (maks: {cfg['maks_durasi_menit']} menit)",
                suhu_udara, kelembaban_tanah, durasi_nyala)
            return _response_state("mati", f"Pompa dimatikan setelah {durasi_nyala} menit penyiraman", "dimatikan")

        # Rule 6 — Histeresis: jika sudah cukup basah, matikan
        if kelembaban_tanah is not None and kelembaban_tanah >= cfg["kelembaban_mati"]:
            _set_state("mati", f"Kelembaban {kelembaban_tanah}% mencapai target {cfg['kelembaban_mati']}%")
            catat_log_pompa(db, sesi_id, "mati", "otomatis",
                f"Pompa dimatikan karena tanah sudah cukup basah ({kelembaban_tanah}%)",
                suhu_udara, kelembaban_tanah, durasi_nyala)
            return _response_state("mati", f"Target kelembaban {cfg['kelembaban_mati']}% tercapai", "dimatikan")

        # Masih nyala dan belum melebihi durasi / target — biarkan
        sisa = cfg["maks_durasi_menit"] - durasi_nyala
        return _response_state("nyala", f"Pompa sedang menyiram — sisa ±{sisa} menit atau hingga {cfg['kelembaban_mati']}% RH")

    # Rule 7 — masih dalam periode jeda setelah mati
    if _state_pompa["mati_sejak"]:
        jeda_berlalu = _hitung_durasi_menit(_state_pompa["mati_sejak"])
        if jeda_berlalu < cfg["jeda_setelah_menit"]:
            sisa_jeda = cfg["jeda_setelah_menit"] - jeda_berlalu
            return _response_state("mati", f"Dalam periode jeda — pompa bisa nyala lagi dalam {sisa_jeda} menit")

    # Rule 8 — kelembaban tanah rendah
    if kelembaban_tanah is not None and kelembaban_tanah < cfg["kelembaban_nyala"]:
        alasan = f"Kelembaban tanah {kelembaban_tanah}% di bawah threshold {cfg['kelembaban_nyala']}%"
        _set_state("nyala", alasan)
        _state_pompa["panas_sejak"] = None
        catat_log_pompa(db, sesi_id, "nyala", "otomatis", alasan, suhu_udara, kelembaban_tanah)
        return _response_state("nyala", alasan, "dinyalakan")

    # Rule 9 — suhu tinggi berkepanjangan
    if suhu_udara is not None and suhu_udara > cfg["suhu_nyala"]:
        if _state_pompa["panas_sejak"] is None:
            _state_pompa["panas_sejak"] = now
        durasi_panas = _hitung_durasi_menit(_state_pompa["panas_sejak"])
        if durasi_panas >= cfg["durasi_panas_menit"]:
            alasan = (
                f"Suhu {suhu_udara}°C melebihi {cfg['suhu_nyala']}°C "
                f"selama {durasi_panas} menit (threshold: {cfg['durasi_panas_menit']} menit)"
            )
            _set_state("nyala", alasan)
            _state_pompa["panas_sejak"] = None
            catat_log_pompa(db, sesi_id, "nyala", "otomatis", alasan, suhu_udara, kelembaban_tanah)
            return _response_state("nyala", alasan, "dinyalakan")
        else:
            sisa = cfg["durasi_panas_menit"] - durasi_panas
            return _response_state(
                "mati",
                f"Suhu {suhu_udara}°C panas — pompa akan nyala jika bertahan {sisa} menit lagi"
            )
    else:
        # Reset timer panas jika suhu sudah turun
        _state_pompa["panas_sejak"] = None

    return _response_state("mati", "Kondisi normal — pompa tidak diperlukan")


def kontrol_manual(
    db:        Session,
    sesi_id:   str,
    perintah:  str,   # "nyala" | "mati"
    alasan:    str = "Override manual oleh operator",
) -> dict:
    """
    Operator mengambil alih kontrol pompa secara manual dari dashboard.
    Perintah manual mengalahkan logika otomatis.
    """
    if perintah not in ("nyala", "mati"):
        return {"sukses": False, "error": "Perintah tidak valid. Gunakan: nyala | mati"}

    status_baru = f"manual_{perintah}"
    _state_pompa["override_manual"] = True
    _set_state(status_baru, alasan)

    catat_log_pompa(db, sesi_id, status_baru, "manual", alasan)
    return {
        "sukses":      True,
        "status_baru": status_baru,
        "alasan":      alasan,
        "waktu":       datetime.now().isoformat(),
    }


def kembalikan_ke_otomatis(db: Session, sesi_id: str) -> dict:
    """Kembalikan kontrol pompa ke mode otomatis setelah override manual."""
    _state_pompa["override_manual"] = False
    _set_state("mati", "Dikembalikan ke mode otomatis")
    catat_log_pompa(db, sesi_id, "mati", "otomatis", "Dikembalikan ke mode otomatis")
    return {"sukses": True, "pesan": "Pompa kembali ke mode otomatis"}


def get_status_pompa(db: Session) -> dict:
    """Ambil status pompa saat ini beserta info tambahan."""
    durasi = 0
    if _state_pompa["status"] in ("nyala", "manual_nyala") and _state_pompa["nyala_sejak"]:
        durasi = _hitung_durasi_menit(_state_pompa["nyala_sejak"])

    cfg = get_konfigurasi(db)
    return {
        "status":          _state_pompa["status"],
        "override_manual": _state_pompa["override_manual"],
        "nyala_sejak":     _state_pompa["nyala_sejak"].isoformat() if _state_pompa["nyala_sejak"] else None,
        "durasi_nyala_menit": durasi,
        "alasan_terakhir": _state_pompa["alasan_terakhir"],
        "konfigurasi": {
            "mode":               cfg["mode"],
            "suhu_nyala":         cfg["suhu_nyala"],
            "kelembaban_nyala":   cfg["kelembaban_nyala"],
            "kelembaban_mati":    cfg["kelembaban_mati"],
            "durasi_panas_menit": cfg["durasi_panas_menit"],
            "maks_durasi_menit":  cfg["maks_durasi_menit"],
            "jam_operasional":    f"{cfg['aktif_jam_mulai']}–{cfg['aktif_jam_selesai']}",
        },
    }


def ambil_riwayat_pompa(db: Session, limit: int = 30) -> list:
    """Ambil log aktivitas pompa untuk ditampilkan di dashboard."""
    rows = db.execute(text("""
        SELECT status, trigger_oleh, alasan, suhu_saat_itu,
               kelembaban_saat_itu, durasi_menit, dicatat_pada
        FROM log_pompa
        ORDER BY dicatat_pada DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        {
            "status":       row[0],
            "trigger_oleh": row[1],
            "alasan":       row[2],
            "suhu":         row[3],
            "kelembaban":   row[4],
            "durasi_menit": row[5],
            "dicatat_pada": str(row[6]),
        }
        for row in rows
    ]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _set_state(status: str, alasan: str):
    now = datetime.now()
    _state_pompa["alasan_terakhir"] = alasan
    if status in ("nyala", "manual_nyala"):
        _state_pompa["status"]      = status
        _state_pompa["nyala_sejak"] = now
        _state_pompa["mati_sejak"]  = None
    else:
        _state_pompa["status"]      = status
        _state_pompa["mati_sejak"]  = now
        _state_pompa["nyala_sejak"] = None


def _hitung_durasi_menit(sejak: datetime) -> int:
    if sejak is None:
        return 0
    return int((datetime.now() - sejak).total_seconds() / 60)


def _response_state(status: str, alasan: str, aksi: str = "tidak_ada") -> dict:
    return {
        "status_pompa":    status,
        "aksi":            aksi,
        "alasan":          alasan,
        "override_manual": _state_pompa["override_manual"],
        "waktu_evaluasi":  datetime.now().isoformat(),
    }