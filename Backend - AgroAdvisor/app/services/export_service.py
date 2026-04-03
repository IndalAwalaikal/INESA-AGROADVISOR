"""
Export Service — Generate CSV untuk Riwayat Data AgriSmart

Mendukung ekspor data riwayat pupuk, pestisida, pompa, dan sensor ke format CSV.
CSV dipilih karena kompatibel dengan Excel dan Google Sheets.
"""
import csv
import io
from sqlalchemy.orm import Session
from sqlalchemy import text


def export_riwayat_pupuk_csv(db: Session) -> bytes:
    """Export semua riwayat rekomendasi pupuk ke CSV."""
    rows = db.execute(text("""
        SELECT r.id, r.sesi_id, r.jenis_tanaman,
               r.kondisi_tanah_ringkasan, r.kesesuaian_tanaman,
               r.estimasi_peningkatan, r.catatan_ai, r.model_ai, r.dibuat_pada
        FROM rekomendasi_pupuk r
        ORDER BY r.dibuat_pada DESC
    """)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Sesi ID", "Jenis Tanaman", "Kondisi Tanah",
        "Kesesuaian", "Estimasi Peningkatan", "Catatan AI", "Model AI", "Tanggal"
    ])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2], row[3],
            row[4], row[5], row[6], row[7], str(row[8]),
        ])

    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def export_riwayat_pestisida_csv(db: Session) -> bytes:
    """Export semua riwayat rekomendasi pestisida ke CSV."""
    rows = db.execute(text("""
        SELECT r.id, r.sesi_id, r.jenis_tanaman, r.jenis_hama,
               r.tingkat_serangan, r.estimasi_efektivitas,
               r.catatan_ai, r.model_ai, r.dibuat_pada
        FROM rekomendasi_pestisida r
        ORDER BY r.dibuat_pada DESC
    """)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Sesi ID", "Jenis Tanaman", "Jenis Hama",
        "Tingkat Serangan", "Estimasi Efektivitas",
        "Catatan AI", "Model AI", "Tanggal"
    ])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2], row[3],
            row[4], row[5], row[6], row[7], str(row[8]),
        ])

    return output.getvalue().encode("utf-8-sig")


def export_riwayat_pompa_csv(db: Session) -> bytes:
    """Export semua riwayat aktivitas pompa ke CSV."""
    rows = db.execute(text("""
        SELECT id, sesi_id, status, trigger_oleh, alasan,
               suhu_saat_itu, kelembaban_saat_itu, durasi_menit, dicatat_pada
        FROM log_pompa
        ORDER BY dicatat_pada DESC
    """)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Sesi ID", "Status", "Trigger Oleh", "Alasan",
        "Suhu (°C)", "Kelembaban (%)", "Durasi (menit)", "Waktu"
    ])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2], row[3], row[4],
            row[5], row[6], row[7], str(row[8]),
        ])

    return output.getvalue().encode("utf-8-sig")


def export_riwayat_sensor_csv(db: Session) -> bytes:
    """Export semua log sensor ke CSV."""
    rows = db.execute(text("""
        SELECT id, sesi_id, device_id, ph_tanah, nitrogen, fosfor, kalium,
               suhu_udara, kelembaban_udara, kelembaban_tanah,
               hujan_terdeteksi, sumber, dicatat_pada
        FROM log_sensor
        ORDER BY dicatat_pada DESC
    """)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Sesi ID", "Device ID", "pH Tanah", "Nitrogen", "Fosfor", "Kalium",
        "Suhu Udara (°C)", "Kelembaban Udara (%)", "Kelembaban Tanah (%)",
        "Hujan", "Sumber", "Waktu"
    ])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2], row[3], row[4], row[5], row[6],
            row[7], row[8], row[9], row[10], row[11], str(row[12]),
        ])

    return output.getvalue().encode("utf-8-sig")
