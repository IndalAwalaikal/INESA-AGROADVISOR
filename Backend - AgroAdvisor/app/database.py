from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "agroadvisor")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine       = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Buat semua tabel jika belum ada."""
    with engine.connect() as conn:

        # Tabel sesi pengujian tanah
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sesi_pengujian (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                sesi_id          VARCHAR(60)  UNIQUE NOT NULL,
                device_id        VARCHAR(100),
                lokasi           VARCHAR(200),
                jenis_tanaman    VARCHAR(100),
                fase_tumbuh      VARCHAR(50),
                luas_lahan       FLOAT DEFAULT 1.0,
                ph_tanah         FLOAT,
                nitrogen         FLOAT,
                fosfor           FLOAT,
                kalium           FLOAT,
                suhu_udara       FLOAT,
                kelembaban_udara FLOAT,
                kelembaban_tanah FLOAT,
                hujan_terdeteksi BOOLEAN DEFAULT FALSE,
                status           VARCHAR(20) DEFAULT 'aktif',
                catatan          TEXT,
                dibuat_pada      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                direset_pada     TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel rekomendasi pupuk
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rekomendasi_pupuk (
                id                      INT AUTO_INCREMENT PRIMARY KEY,
                sesi_id                 VARCHAR(60) NOT NULL,
                jenis_tanaman           VARCHAR(100),
                kondisi_tanah_ringkasan TEXT,
                kesesuaian_tanaman      VARCHAR(20),
                rekomendasi_json        LONGTEXT,
                estimasi_peningkatan    VARCHAR(50),
                catatan_ai              TEXT,
                model_ai                VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',
                dibuat_pada             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sesi    (sesi_id),
                INDEX idx_tanaman (jenis_tanaman),
                INDEX idx_dibuat  (dibuat_pada)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel detail item pupuk
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS detail_pupuk (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                rekomendasi_id   INT NOT NULL,
                sesi_id          VARCHAR(60),
                nama_pupuk       VARCHAR(100),
                bahan_aktif      VARCHAR(200),
                takaran_per_ha   VARCHAR(100),
                takaran_total    VARCHAR(100),
                waktu_aplikasi   VARCHAR(200),
                metode_aplikasi  VARCHAR(200),
                tujuan           TEXT,
                urutan           INT DEFAULT 1,
                dibuat_pada      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_rekomendasi (rekomendasi_id),
                INDEX idx_sesi        (sesi_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel log sensor
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS log_sensor (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                sesi_id           VARCHAR(60),
                device_id         VARCHAR(100),
                ph_tanah          FLOAT,
                nitrogen          FLOAT,
                fosfor            FLOAT,
                kalium            FLOAT,
                suhu_udara        FLOAT,
                kelembaban_udara  FLOAT,
                kelembaban_tanah  FLOAT,
                hujan_terdeteksi  BOOLEAN,
                sumber            VARCHAR(50) DEFAULT 'json_statis',
                dicatat_pada      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sesi    (sesi_id),
                INDEX idx_dicatat (dicatat_pada)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel feedback rekomendasi pupuk
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback_rekomendasi (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                rekomendasi_id   INT NOT NULL,
                jenis_rekomendasi VARCHAR(20) DEFAULT 'pupuk',
                rating           TINYINT NOT NULL,
                catatan_hasil    TEXT,
                dibuat_pada      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_rek (rekomendasi_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Pastikan kolom jenis_rekomendasi ada (migrasi ringan)
        try:
            conn.execute(text("ALTER TABLE feedback_rekomendasi ADD COLUMN jenis_rekomendasi VARCHAR(20) DEFAULT 'pupuk' AFTER rekomendasi_id"))
        except:
            pass

        # Tabel rekomendasi pestisida
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rekomendasi_pestisida (
                id                   INT AUTO_INCREMENT PRIMARY KEY,
                sesi_id              VARCHAR(60) NOT NULL,
                jenis_tanaman        VARCHAR(100),
                jenis_hama           VARCHAR(200),
                tingkat_serangan     VARCHAR(20),
                rekomendasi_json     LONGTEXT,
                estimasi_efektivitas VARCHAR(50),
                catatan_ai           TEXT,
                model_ai             VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',
                dibuat_pada          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sesi    (sesi_id),
                INDEX idx_tanaman (jenis_tanaman),
                INDEX idx_hama    (jenis_hama)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel detail item pestisida
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS detail_pestisida (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                rekomendasi_id   INT NOT NULL,
                sesi_id          VARCHAR(60),
                nama_pestisida   VARCHAR(150),
                bahan_aktif      VARCHAR(200),
                jenis_pestisida  VARCHAR(50),
                dosis_per_liter  VARCHAR(100),
                dosis_per_ha     VARCHAR(100),
                waktu_semprot    VARCHAR(200),
                interval_semprot VARCHAR(100),
                metode_aplikasi  VARCHAR(200),
                phi              VARCHAR(100),
                tujuan           TEXT,
                urutan           INT DEFAULT 1,
                dibuat_pada      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_rekomendasi (rekomendasi_id),
                INDEX idx_sesi        (sesi_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel log status pompa
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS log_pompa (
                id                  INT AUTO_INCREMENT PRIMARY KEY,
                sesi_id             VARCHAR(60),
                status              VARCHAR(20),
                trigger_oleh        VARCHAR(50),
                alasan              TEXT,
                suhu_saat_itu       FLOAT,
                kelembaban_saat_itu FLOAT,
                durasi_menit        INT DEFAULT 0,
                dicatat_pada        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sesi    (sesi_id),
                INDEX idx_status  (status),
                INDEX idx_dicatat (dicatat_pada)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel konfigurasi pompa (1 baris saja, id=1)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS konfigurasi_pompa (
                id                  INT DEFAULT 1 PRIMARY KEY,
                suhu_nyala          FLOAT DEFAULT 33.0,
                durasi_panas_menit  INT   DEFAULT 120,
                kelembaban_nyala    FLOAT DEFAULT 40.0,
                kelembaban_mati     FLOAT DEFAULT 60.0,
                maks_durasi_menit   INT   DEFAULT 45,
                jeda_setelah_menit  INT   DEFAULT 15,
                aktif_jam_mulai     TIME  DEFAULT '05:00:00',
                aktif_jam_selesai   TIME  DEFAULT '17:00:00',
                mode                VARCHAR(20) DEFAULT 'otomatis',
                diperbarui_pada     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Pastikan kolom kelembaban_mati ada (migrasi ringan)
        try:
            conn.execute(text("ALTER TABLE konfigurasi_pompa ADD COLUMN kelembaban_mati FLOAT DEFAULT 60.0 AFTER kelembaban_nyala"))
        except:
            pass

        # Tabel jadwal pompa terjadwal (cron jobs)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jadwal_pompa (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                jam             TIME NOT NULL,
                durasi_menit    INT NOT NULL DEFAULT 15,
                hari            VARCHAR(100) DEFAULT 'semua',
                aktif           BOOLEAN DEFAULT TRUE,
                dibuat_pada     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_aktif (aktif)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel kebutuhan hara tanaman (Master Data)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kebutuhan_hara (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                nama_tanaman VARCHAR(100) UNIQUE NOT NULL,
                n_req        FLOAT NOT NULL,
                p_req        FLOAT NOT NULL,
                k_req        FLOAT NOT NULL,
                ph_min       FLOAT NOT NULL,
                ph_max       FLOAT NOT NULL,
                kebutuhan_air VARCHAR(20) DEFAULT 'Medium',
                dibuat_pada   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # Tabel Master Data Hama & Penyakit (Master Data)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS master_hama_penyakit (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                nama_tanaman    VARCHAR(100) NOT NULL,
                kategori        VARCHAR(50) NOT NULL,
                nama_umum       VARCHAR(200) NOT NULL,
                nama_ilmiah     VARCHAR(200),
                gejala_utama    TEXT,
                saran_produk    TEXT,
                dibuat_pada     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tanaman (nama_tanaman),
                INDEX idx_kategori (kategori)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        conn.commit()
    print("Database dan semua tabel berhasil diinisialisasi")