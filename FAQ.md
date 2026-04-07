# ❓ FAQ — Pertanyaan Umum AgroAdvisor

## 📋 Daftar Isi
1. [Umum](#1-umum)
2. [Instalasi & Deployment](#2-instalasi--deployment)
3. [Sistem AI & Rekomendasi](#3-sistem-ai--rekomendasi)
4. [Pompa & Irigasi Otomatis](#4-pompa--irigasi-otomatis)
5. [IoT & Sensor](#5-iot--sensor)
6. [Cuaca & Deteksi Hujan](#6-cuaca--deteksi-hujan)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Umum

### Apa itu AgroAdvisor?
AgroAdvisor adalah **Sistem Rekomendasi Pertanian Cerdas** berbasis IoT dan AI yang membantu petani mengambil keputusan tepat mengenai **pemupukan**, **pengendalian hama (pestisida)**, dan **irigasi otomatis** berdasarkan data sensor tanah secara real-time.

### Teknologi apa yang digunakan?
| Komponen | Teknologi |
|---|---|
| Backend API | Python, FastAPI, Gunicorn |
| Frontend Dashboard | Next.js (React), TypeScript |
| Database | MySQL 8.0 |
| AI Cloud | Google Gemini, Groq |
| AI Lokal (Fallback) | Ollama + Qwen 2.5 (7B) |
| Perangkat IoT | ESP32, Sensor DHT22, NPK RS485 |
| Cuaca | OpenWeatherMap API |
| Containerization | Docker & Docker Compose |
| Reverse Proxy | Nginx |

### Siapa yang bisa mengakses dashboard?
Dashboard sensor bersifat **publik** — siapa saja bisa melihat data sensor dan status pompa tanpa login. Namun, halaman **Admin** (pengaturan sistem) dilindungi oleh kredensial yang diatur di file `.env`.

---

## 2. Instalasi & Deployment

### Bagaimana cara menjalankan sistem ini?
```bash
# 1. Clone repository
git clone https://github.com/IndalAwalaikal/INESA-AGROADVISOR.git
cd INESA-AGROADVISOR

# 2. Salin dan isi file environment
cp "Backend - AgroAdvisor/.env.example" "Backend - AgroAdvisor/.env"
# Edit .env dan isi API key Anda

# 3. Jalankan semua layanan
docker compose up -d --build

# 4. Akses dashboard
# Frontend  : http://localhost:3000
# Backend   : http://localhost:8001/docs
# Via Nginx : http://localhost:8080
```

### Apa saja yang perlu diisi di file `.env`?
| Variabel | Keterangan | Wajib? |
|---|---|---|
| `GEMINI_API_KEY` | API Key Google Gemini untuk AI | ✅ Ya |
| `GROQ_API_KEY` | API Key Groq untuk AI cadangan | ✅ Ya |
| `OPENWEATHER_API_KEY` | API Key OpenWeatherMap | ✅ Ya |
| `OPENWEATHER_LAT` / `LON` | Koordinat lokasi lahan | ✅ Ya |
| `DB_PASSWORD` | Password database MySQL | Opsional (default: password123) |
| `ADMIN_USERNAME` / `PASSWORD` | Kredensial admin dashboard | Opsional |

### Mengapa saat di-pull di komputer lain, AI tidak berfungsi?
Karena file `.env` **tidak ikut tersimpan di Git** (demi keamanan). Anda harus membuat ulang file `.env` dari template `.env.example` dan mengisi semua API key secara manual di setiap komputer baru.

### Berapa lama waktu startup pertama kali?
Startup pertama membutuhkan waktu **10–30 menit** karena:
- Docker mengunduh semua image (MySQL, Ollama, Python, Node.js)
- Model AI lokal Qwen 2.5 (±4.7 GB) diunduh otomatis oleh container `ollama-init`
- Frontend Next.js melakukan build production

Startup selanjutnya hanya membutuhkan ±30 detik.

---

## 3. Sistem AI & Rekomendasi

### AI apa yang digunakan untuk rekomendasi?
Sistem menggunakan **3 lapis AI fallback** secara berurutan:
1. **Google Gemini** (Cloud) — prioritas utama, tercepat
2. **Groq** (Cloud) — cadangan jika Gemini limit/error
3. **Ollama Qwen 2.5** (Lokal) — cadangan terakhir, berjalan di server sendiri

Jika satu provider gagal, sistem otomatis berpindah ke provider berikutnya tanpa intervensi pengguna.

### Mengapa rekomendasi AI muncul error "Internal Server Error"?
Kemungkinan penyebab:
- **API key kosong atau tidak valid** — periksa `.env`
- **Kuota API habis** — Gemini dan Groq memiliki batas harian pada tier gratis
- **Ollama belum siap** — model masih dalam proses download (cek: `docker logs agroadvisor-ollama-init`)

### Rekomendasi apa saja yang tersedia?
1. **Rekomendasi Pupuk** — berdasarkan pH tanah, nitrogen (N), fosfor (P), dan kalium (K) yang terukur oleh sensor
2. **Saran Tanaman** — jenis tanaman yang cocok untuk kondisi tanah saat ini
3. **Rekomendasi Pestisida** — pengendalian hama berbasis PHT (Pengendalian Hama Terpadu) dengan informasi PHI (Pre-Harvest Interval)

### Apakah rekomendasi bisa di-download?
Ya, setiap rekomendasi pupuk dan pestisida bisa diunduh dalam format **PDF** melalui tombol download di halaman riwayat. Data riwayat juga bisa diekspor ke **CSV**.

---

## 4. Pompa & Irigasi Otomatis

### Bagaimana cara kerja pompa otomatis?
Sistem menggunakan **Rule Engine** dengan urutan prioritas:
1. Jika **mode manual** → operator yang mengontrol
2. Jika **mode nonaktif** → pompa selalu mati
3. Jika **hujan terdeteksi** (dari OpenWeather API) → pompa dihentikan
4. Jika **hujan diprediksi** dalam 2 jam ke depan → pompa ditunda
5. Jika **di luar jam operasional** → pompa mati
6. Jika **kelembaban tanah < ambang nyala** → pompa menyala
7. Jika **kelembaban tanah > ambang mati** → pompa dimatikan (histeresis)
8. Jika **durasi menyala > maks durasi** → pompa dimatikan otomatis

### Ada berapa mode pompa?
| Mode | Keterangan |
|---|---|
| **Otomatis** | Rule engine AI yang mengendalikan berdasarkan sensor & cuaca |
| **Manual** | Operator menyalakan/matikan pompa secara langsung dari dashboard |
| **Terjadwal** | Pompa menyala pada jam-jam tertentu yang sudah dijadwalkan |
| **Nonaktif** | Pompa selalu mati (untuk maintenance) |

### Mengapa pompa tidak bisa diganti mode atau disimpan pengaturannya?
Pastikan:
- Backend sudah berjalan (`docker logs agroadvisor-backend` tidak ada error)
- Buka dashboard melalui **Nginx** (port 8080) bukan langsung port 3000, agar CORS tidak memblokir request

### Apa itu ambang batas nyala dan ambang batas mati?
- **Ambang Batas Nyala** (contoh: 32%) — pompa akan **menyala** jika kelembaban tanah turun **di bawah** nilai ini
- **Ambang Batas Mati** (contoh: 60%) — pompa akan **mati** jika kelembaban tanah naik **di atas** nilai ini

Perbedaan antara keduanya mencegah pompa menyala-mati terus-menerus (disebut **histeresis**).

---

## 5. IoT & Sensor

### Sensor apa saja yang digunakan?
| Sensor | Data yang Diukur |
|---|---|
| DHT22 | Suhu udara, kelembaban udara |
| NPK Sensor (RS485/Modbus) | Nitrogen, fosfor, kalium, pH tanah, kelembaban tanah, EC, suhu tanah |

### Bagaimana alat IoT mengirim data ke server?
ESP32 mengirim data sensor melalui **HTTP POST** ke endpoint:
```
POST /api/iot/sensor
```
Dengan payload JSON:
```json
{
  "device_id": "esp32_lahan_6509",
  "suhu_udara": 30.3,
  "kelembaban_udara": 82.3,
  "ph_tanah": 6.2,
  "nitrogen": 160,
  "fosfor": 28,
  "kalium": 102,
  "kelembaban_tanah": 34
}
```
Server akan membalas dengan perintah pompa (`"pump": "on"` atau `"pump": "off"`) yang dieksekusi oleh relay di ESP32.

### Berapa interval pengiriman data sensor?
Default: setiap **10 detik** (dapat diubah di kode firmware ESP32). Evaluasi pompa oleh scheduler backend berjalan setiap **30 detik**.

---

## 6. Cuaca & Deteksi Hujan

### Dari mana data cuaca diperoleh?
Data cuaca diperoleh secara real-time dari **OpenWeatherMap API** (tier gratis). Sistem mengambil data cuaca tiap **10 menit** dan menyimpannya di cache.

### Apakah sistem menggunakan sensor hujan fisik?
**Tidak.** Sistem sepenuhnya mengandalkan data API OpenWeatherMap untuk mendeteksi kondisi hujan saat ini dan prakiraan hujan ke depan. Sensor hujan fisik telah dihapus dari arsitektur.

### Bagaimana deteksi hujan mempengaruhi pompa?
- Jika **sedang hujan** → pompa otomatis dimatikan untuk menghemat air dan listrik
- Jika **diprediksi hujan** dalam 2 jam → pompa ditunda (menunggu maksimal 60 menit)
- Jika setelah 60 menit hujan tidak kunjung datang dan tanah tetap kering → pompa menyala

### Bagaimana mengubah lokasi cuaca?
Edit variabel berikut di file `.env`:
```env
OPENWEATHER_LAT=-3.45    # Ganti dengan latitude lahan Anda
OPENWEATHER_LON=119.67   # Ganti dengan longitude lahan Anda
```
Kemudian restart backend: `docker restart agroadvisor-backend`

---

## 7. Troubleshooting

### Port 80 sudah digunakan saat menjalankan Nginx
Port 80 kemungkinan dipakai oleh Apache (XAMPP). Solusi:
- Matikan Apache terlebih dahulu, **atau**
- Nginx sudah dikonfigurasi di port **8080** sebagai alternatif

### Database error "Data too long for column"
Kolom database untuk respons AI sudah diubah ke tipe `TEXT`. Jika masih terjadi, jalankan:
```bash
docker exec -it agroadvisor-db mysql -u root -ppassword123 agroadvisor -e "
  ALTER TABLE rekomendasi_pupuk MODIFY estimasi_peningkatan TEXT;
  ALTER TABLE rekomendasi_pestisida MODIFY estimasi_efektivitas TEXT;
"
```

### WebSocket tidak terhubung (dashboard tidak real-time)
- Pastikan mengakses dashboard melalui **Nginx** (port 8080 atau domain)
- Cek bahwa backend berjalan: `docker logs agroadvisor-backend`
- WebSocket membutuhkan koneksi yang stabil; gunakan browser modern (Chrome/Firefox)

### Bagaimana cara melihat log sistem?
```bash
# Log backend
docker logs -f agroadvisor-backend

# Log database
docker logs -f agroadvisor-db

# Log Nginx
docker logs -f agroadvisor-nginx

# Log Ollama (AI lokal)
docker logs -f agroadvisor-ollama

# Status semua container
docker compose ps
```

### Bagaimana cara reset total dan mulai dari awal?
```bash
# Hentikan semua container
docker compose down

# Hapus semua data (database, model AI)
docker compose down -v

# Rebuild dan jalankan ulang
docker compose up -d --build
```

> ⚠️ **Peringatan:** Perintah `docker compose down -v` akan menghapus **semua data database** termasuk riwayat rekomendasi dan log pompa.

---

*Dokumen ini dibuat untuk proyek **AgroAdvisor — INESA Rajang 2026**.*
*Terakhir diperbarui: 7 April 2026*
