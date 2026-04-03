-- =====================================================
-- AGROADVISOR DATABASE SCHEMA
-- Smart Farming AI System
-- =====================================================

CREATE DATABASE IF NOT EXISTS agroadvisor
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE agroadvisor;

-- =====================================================
-- TABEL SESI PENGUJIAN TANAH
-- =====================================================

CREATE TABLE IF NOT EXISTS sesi_pengujian (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesi_id VARCHAR(60) UNIQUE NOT NULL,
    device_id VARCHAR(100),
    lokasi VARCHAR(200),
    jenis_tanaman VARCHAR(100),
    fase_tumbuh VARCHAR(50),
    luas_lahan FLOAT DEFAULT 1.0,

    ph_tanah FLOAT,
    nitrogen FLOAT,
    fosfor FLOAT,
    kalium FLOAT,

    suhu_udara FLOAT,
    kelembaban_udara FLOAT,
    kelembaban_tanah FLOAT,
    hujan_terdeteksi BOOLEAN DEFAULT FALSE,

    status VARCHAR(20) DEFAULT 'aktif',
    catatan TEXT,

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    direset_pada TIMESTAMP NULL,

    INDEX idx_sesi_id (sesi_id),
    INDEX idx_device (device_id),
    INDEX idx_tanaman (jenis_tanaman),
    INDEX idx_status (status),
    INDEX idx_created (dibuat_pada)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL LOG SENSOR IOT
-- =====================================================

CREATE TABLE IF NOT EXISTS log_sensor (

    id INT AUTO_INCREMENT PRIMARY KEY,

    sesi_id VARCHAR(60),
    device_id VARCHAR(100),

    ph_tanah FLOAT,
    nitrogen FLOAT,
    fosfor FLOAT,
    kalium FLOAT,

    suhu_udara FLOAT,
    kelembaban_udara FLOAT,
    kelembaban_tanah FLOAT,

    hujan_terdeteksi BOOLEAN,

    sumber VARCHAR(50) DEFAULT 'json_statis',

    dicatat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sensor_sesi (sesi_id),
    INDEX idx_sensor_device (device_id),
    INDEX idx_sensor_time (dicatat_pada),

    FOREIGN KEY (sesi_id)
        REFERENCES sesi_pengujian(sesi_id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL REKOMENDASI PUPUK (AI)
-- =====================================================

CREATE TABLE IF NOT EXISTS rekomendasi_pupuk (

    id INT AUTO_INCREMENT PRIMARY KEY,

    sesi_id VARCHAR(60) NOT NULL,
    jenis_tanaman VARCHAR(100),

    kondisi_tanah_ringkasan TEXT,
    kesesuaian_tanaman VARCHAR(20),

    rekomendasi_json LONGTEXT,
    estimasi_peningkatan TEXT,

    catatan_ai TEXT,

    model_ai VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_rek_pupuk_sesi (sesi_id),
    INDEX idx_rek_pupuk_tanaman (jenis_tanaman),
    INDEX idx_rek_pupuk_created (dibuat_pada),

    FOREIGN KEY (sesi_id)
        REFERENCES sesi_pengujian(sesi_id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL DETAIL PUPUK
-- =====================================================

CREATE TABLE IF NOT EXISTS detail_pupuk (

    id INT AUTO_INCREMENT PRIMARY KEY,

    rekomendasi_id INT NOT NULL,
    sesi_id VARCHAR(60),

    nama_pupuk VARCHAR(255),
    bahan_aktif TEXT,

    takaran_per_ha TEXT,
    takaran_total TEXT,

    waktu_aplikasi TEXT,
    metode_aplikasi TEXT,

    tujuan TEXT,

    urutan INT DEFAULT 1,

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_detail_pupuk_rekomendasi (rekomendasi_id),
    INDEX idx_detail_pupuk_sesi (sesi_id),

    FOREIGN KEY (rekomendasi_id)
        REFERENCES rekomendasi_pupuk(id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL FEEDBACK REKOMENDASI
-- =====================================================

CREATE TABLE IF NOT EXISTS feedback_rekomendasi (

    id INT AUTO_INCREMENT PRIMARY KEY,

    rekomendasi_id INT NOT NULL,
    rating TINYINT NOT NULL,

    catatan_hasil TEXT,

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_feedback_rek (rekomendasi_id),
    INDEX idx_feedback_rating (rating),

    FOREIGN KEY (rekomendasi_id)
        REFERENCES rekomendasi_pupuk(id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL REKOMENDASI PESTISIDA
-- =====================================================

CREATE TABLE IF NOT EXISTS rekomendasi_pestisida (

    id INT AUTO_INCREMENT PRIMARY KEY,

    sesi_id VARCHAR(60) NOT NULL,
    jenis_tanaman VARCHAR(100),

    jenis_hama VARCHAR(200),
    tingkat_serangan VARCHAR(20),

    rekomendasi_json LONGTEXT,

    estimasi_efektivitas TEXT,

    catatan_ai TEXT,

    model_ai VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_pestisida_sesi (sesi_id),
    INDEX idx_pestisida_tanaman (jenis_tanaman),
    INDEX idx_pestisida_hama (jenis_hama),
    INDEX idx_pestisida_created (dibuat_pada),

    FOREIGN KEY (sesi_id)
        REFERENCES sesi_pengujian(sesi_id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL DETAIL PESTISIDA
-- =====================================================

CREATE TABLE IF NOT EXISTS detail_pestisida (

    id INT AUTO_INCREMENT PRIMARY KEY,

    rekomendasi_id INT NOT NULL,
    sesi_id VARCHAR(60),

    nama_pestisida VARCHAR(255),
    bahan_aktif TEXT,

    jenis_pestisida VARCHAR(150),

    dosis_per_liter TEXT,
    dosis_per_ha TEXT,

    waktu_semprot TEXT,
    interval_semprot TEXT,

    metode_aplikasi TEXT,

    phi TEXT,

    tujuan TEXT,

    urutan INT DEFAULT 1,

    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_detail_pestisida_rek (rekomendasi_id),
    INDEX idx_detail_pestisida_sesi (sesi_id),

    FOREIGN KEY (rekomendasi_id)
        REFERENCES rekomendasi_pestisida(id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL LOG POMPA IRIGASI
-- =====================================================

CREATE TABLE IF NOT EXISTS log_pompa (

    id INT AUTO_INCREMENT PRIMARY KEY,

    sesi_id VARCHAR(60),

    status VARCHAR(20),

    trigger_oleh VARCHAR(50),

    alasan TEXT,

    suhu_saat_itu FLOAT,
    kelembaban_saat_itu FLOAT,

    durasi_menit INT DEFAULT 0,

    dicatat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_pompa_sesi (sesi_id),
    INDEX idx_pompa_status (status),
    INDEX idx_pompa_time (dicatat_pada)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- TABEL KONFIGURASI POMPA
-- =====================================================

CREATE TABLE IF NOT EXISTS konfigurasi_pompa (

    id INT DEFAULT 1 PRIMARY KEY,

    suhu_nyala FLOAT DEFAULT 33.0,
    durasi_panas_menit INT DEFAULT 120,

    kelembaban_nyala FLOAT DEFAULT 40.0,

    maks_durasi_menit INT DEFAULT 45,
    jeda_setelah_menit INT DEFAULT 15,

    aktif_jam_mulai TIME DEFAULT '05:00:00',
    aktif_jam_selesai TIME DEFAULT '17:00:00',

    mode VARCHAR(20) DEFAULT 'otomatis',

    diperbarui_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =====================================================
-- INSERT DEFAULT CONFIG
-- =====================================================

INSERT IGNORE INTO konfigurasi_pompa (id) VALUES (1);