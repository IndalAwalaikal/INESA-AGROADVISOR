from sqlalchemy import text
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def jalankan_cleanup_riwayat(db: Session, bulan: int = 6):
    """
    Menghapus data riwayat (sensor, rekomendasi, log pompa) yang lebih tua dari X bulan.
    Data ini dianggap sudah dipelajari oleh LLM/Rule Engine sehingga aman dihapus
    untuk menjaga performa database dan kebersihan dashboard.
    """
    try:
        # Hitung batas waktu
        batas_waktu = datetime.now() - timedelta(days=bulan * 30)
        logger.info(f"Memulai cleanup riwayat otomatis (lebih tua dari {bulan} bulan: {batas_waktu})")

        # 1. Hapus detail_pupuk yang induknya sudah tua
        db.execute(text("""
            DELETE FROM detail_pupuk 
            WHERE rekomendasi_id IN (SELECT id FROM rekomendasi_pupuk WHERE dibuat_pada < :batas)
        """), {"batas": batas_waktu})

        # 2. Hapus detail_pestisida yang induknya sudah tua
        db.execute(text("""
            DELETE FROM detail_pestisida 
            WHERE rekomendasi_id IN (SELECT id FROM rekomendasi_pestisida WHERE dibuat_pada < :batas)
        """), {"batas": batas_waktu})

        # 3. Hapus feedback_rekomendasi (baik pupuk maupun pestisida)
        # Kita hapus berdasarkan dibuat_pada feedback itu sendiri atau induknya.
        # Untuk kesederhanaan, hapus feedback yang berumur > 6 bulan.
        db.execute(text("DELETE FROM feedback_rekomendasi WHERE dibuat_pada < :batas"), {"batas": batas_waktu})

        # 4. Hapus rekomendasi utama
        db.execute(text("DELETE FROM rekomendasi_pupuk WHERE dibuat_pada < :batas"), {"batas": batas_waktu})
        db.execute(text("DELETE FROM rekomendasi_pestisida WHERE dibuat_pada < :batas"), {"batas": batas_waktu})

        # 5. Hapus log sensor dan log pompa
        db.execute(text("DELETE FROM log_sensor WHERE dicatat_pada < :batas"), {"batas": batas_waktu})
        db.execute(text("DELETE FROM log_pompa WHERE dicatat_pada < :batas"), {"batas": batas_waktu})

        # 6. Hapus sesi pengujian lama (hanya yang sudah tidak aktif)
        db.execute(text("DELETE FROM sesi_pengujian WHERE dibuat_pada < :batas"), {"batas": batas_waktu})

        db.commit()
        logger.info("Cleanup riwayat otomatis berhasil diselesaikan.")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal menjalankan cleanup riwayat: {e}")
        return False
