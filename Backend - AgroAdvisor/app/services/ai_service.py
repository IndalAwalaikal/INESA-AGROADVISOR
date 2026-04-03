import os
import json
import logging
import asyncio
from google import genai
from google.genai import types
from groq import AsyncGroq
from app.services.rule_engine import hitung_dosis_pupuk
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# GROQ_API_KEY might be empty initially, AsyncGroq might handle it but better to guard
groq_key = os.getenv("GROQ_API_KEY")
groq_client = AsyncGroq(api_key=groq_key) if groq_key else None

# Daftar model untuk fallback (berurutan dari priorititas tertinggi)
MODELS_FALLBACK = [
    'gemini-2.5-flash-lite', 
    'gemini-2.5-flash', 
    'gemini-flash-latest',
    'gemini-2.0-flash-lite', 
    'gemini-2.0-flash', 
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
    'groq/llama-3.3-70b-versatile'
]

# ─── Profil Kebutuhan Spesifik Per Tanaman ────────────────────────────────────
PROFIL_TANAMAN = {
    "padi": {
        "ph_ideal": "6.0–7.0",
        "n": "tinggi",
        "p": "sedang",
        "k": "sedang",
        "catatan": (
            "N tinggi di fase vegetatif untuk pertumbuhan anakan, "
            "P penting saat pembentukan akar dan bunting, "
            "K meningkat di fase pengisian bulir untuk ketegaran batang dan kualitas gabah."
        ),
    },
    "jagung": {
        "ph_ideal": "5.8–7.0",
        "n": "tinggi",
        "p": "tinggi",
        "k": "sedang",
        "catatan": (
            "Sangat responsif terhadap N — kekurangan N terlihat dari daun menguning mulai bawah, "
            "P sangat penting untuk perkembangan akar dan pembentukan tongkol, "
            "K untuk ketegaran batang dan mencegah rebah."
        ),
    },
    "cabai": {
        "ph_ideal": "6.0–7.0",
        "n": "sedang",
        "p": "tinggi",
        "k": "tinggi",
        "catatan": (
            "K tinggi sangat penting untuk kualitas, ukuran, and ketahanan buah, "
            "P untuk perakaran and pembungaan, "
            "hindari N berlebihan — menyebabkan tanaman terlalu rimbun and buah sedikit. "
            "Perhatikan juga Ca and Mg untuk mencegah blossom end rot."
        ),
    },
    "tomat": {
        "ph_ideal": "6.0–6.8",
        "n": "sedang",
        "p": "tinggi",
        "k": "tinggi",
        "catatan": (
            "Keseimbangan N-K sangat kritis — N tinggi saat vegetatif lalu dikurangi saat berbunga, "
            "K tinggi saat pembentukan and pematangan buah untuk rasa and ketahanan simpan, "
            "P untuk perakaran kuat. Rentan blossom end rot jika Ca kurang."
        ),
    },
    "singkong": {
        "ph_ideal": "5.5–6.5",
        "n": "rendah",
        "p": "rendah",
        "k": "tinggi",
        "catatan": (
            "K sangat penting untuk pembentukan and pembesaran umbi, "
            "toleran tanah miskin hara N and P, "
            "pupuk berlebihan justru mendorong pertumbuhan daun bukan umbi."
        ),
    },
    "kedelai": {
        "ph_ideal": "6.0–7.0",
        "n": "rendah",
        "p": "tinggi",
        "k": "sedang",
        "catatan": (
            "Mampu fiksasi N dari udara via bakteri Rhizobium — tidak perlu banyak pupuk N, "
            "P sangat penting untuk pembentukan bintil akar and pengisian polong, "
            "anjurkan inokulasi benih dengan Rhizobium sebelum tanam."
        ),
    },
    "bawang_merah": {
        "ph_ideal": "6.0–7.0",
        "n": "sedang",
        "p": "sedang",
        "k": "tinggi",
        "catatan": (
            "K tinggi kritis untuk pembentukan and pembesaran umbi, "
            "N berlebihan membuat daun tumbuh terus and umbi kecil, "
            "P untuk perakaran yang kuat di tanah berpasir."
        ),
    },
    "kentang": {
        "ph_ideal": "5.0–6.0",
        "n": "tinggi",
        "p": "tinggi",
        "k": "tinggi",
        "catatan": (
            "Kebutuhan NPK semuanya tinggi and seimbang, "
            "toleran pH sedikit asam — jangan kapur terlalu tinggi karena bisa picu scab, "
            "K sangat penting untuk ukuran and kualitas umbi."
        ),
    },
    "semangka": {
        "ph_ideal": "6.0–7.0",
        "n": "sedang",
        "p": "sedang",
        "k": "tinggi",
        "catatan": (
            "K tinggi untuk kualitas rasa, kemanisan, and ketebalan kulit buah, "
            "kurangi N saat fase generatif agar energi dialihkan ke buah, "
            "P untuk perakaran and pembungaan awal."
        ),
    },
    "kangkung": {
        "ph_ideal": "5.5–7.0",
        "n": "tinggi",
        "p": "rendah",
        "k": "rendah",
        "catatan": (
            "Fokus utama N untuk pertumbuhan daun yang cepat and hijau, "
            "siklus panen pendek sehingga tidak butuh P-K tinggi, "
            "cocok untuk tanah dengan berbagai kondisi."
        ),
    },
    "sawit": {
        "ph_ideal": "4.0–6.0",
        "n": "tinggi",
        "p": "sedang",
        "k": "tinggi",
        "catatan": (
            "Toleran pH sangat asam — bahkan tumbuh optimal di pH 4-5, "
            "K sangat tinggi untuk produksi Tandan Buah Segar (TBS), "
            "perlu pupuk Mg (Kieserit) karena sering defisiensi di lahan gambut."
        ),
    },
    "tebu": {
        "ph_ideal": "6.0–7.5",
        "n": "tinggi",
        "p": "sedang",
        "k": "tinggi",
        "catatan": (
            "N untuk pertumbuhan batang yang tinggi and cepat, "
            "K untuk akumulasi sukrosa and rendemen gula, "
            "kurangi N mendekati panen agar kadar gula maksimal."
        ),
    },
}

def get_profil_tanaman(jenis_tanaman: str) -> dict:
    kunci = jenis_tanaman.lower().strip()
    return PROFIL_TANAMAN.get(kunci, {
        "ph_ideal": "6.0–7.0",
        "n": "sedang",
        "p": "sedang",
        "k": "sedang",
        "catatan": f"Gunakan kebutuhan NPK umum sebagai acuan untuk tanaman {jenis_tanaman}.",
    })

SYSTEM_PROMPT_PUPUK = """Kamu adalah Dr. Agro, ahli agronomi and ilmu tanah berpengalaman 20 tahun \
di Indonesia, spesialis pertanian presisi berbasis data sensor.

CARA KERJAMU:
1. Baca data kondisi tanah aktual dari sensor IoT
2. Bandingkan dengan profil kebutuhan SPESIFIK tanaman yang dipilih petani
3. Identifikasi GAP: unsur apa yang kurang, berlebih, atau sudah ideal
4. Susun rekomendasi pupuk yang tepat sasaran untuk menutup gap tersebut
5. Jika ada riwayat data lahan, kenali polanya and perbaiki akurasi rekomendasi

PRINSIP REKOMENDASI:
- Rekomendasi HARUS spesifik per tanaman
- WAJIB prioritaskan pupuk SUBSIDI: Urea, NPK Phonska, SP-36, ZA.
- Berikan takaran dosis dalam "karung" (1 karung = 50 kg) and kg/ha.
- Gunakan bahasa yang SUPER SEDERHANA, merakyat, and mudah dipahami.

FORMAT OUTPUT — balas HANYA dengan JSON valid ini:
{
  "kesesuaian_tanaman": {
    "skor": "cocok | cukup_cocok | kurang_cocok",
    "penjelasan": "string",
    "tantangan_utama": ["string"],
    "tanaman_alternatif": ["string"]
  },
  "kondisi_ringkasan": "string",
  "analisis_gap": {
    "ph": "string",
    "nitrogen": "string",
    "fosfor": "string",
    "kalium": "string"
  },
  "daftar_pupuk": [
    {
      "urutan": 1,
      "nama_pupuk": "string",
      "bahan_aktif": "string",
      "takaran_per_ha": "string",
      "takaran_total": "string",
      "waktu_aplikasi": "string",
      "metode_aplikasi": "string",
      "tujuan": "string"
    }
  ],
  "jadwal_aplikasi": "string",
  "estimasi_peningkatan": "string",
  "catatan_penting": "string",
  "peringatan": ["string"],
  "pembelajaran_dari_riwayat": "string"
}"""

SYSTEM_PROMPT_ALUR2 = """Kamu adalah Dr. Agro, ahli agronomi and ilmu tanah berpengalaman 20 tahun di Indonesia.
Tugasmu adalah memberikan saran komprehensif (Alur 2) yang merangkum perhitungan dosis pupuk dari sistem (Rule Engine) untuk as many tanaman (sebanyak-banyaknya, misal 5-8 tanaman) yang paling cocok ditanam berdasarkan kondisi tanah saat ini.

CARA KERJAMU:
1. Baca perhitungan dosis pupuk yang sudah dihitung oleh Rule Engine untuk berbagai tanaman spesifik.
2. Rangkum dosis-dosis tersebut secara jelas dan mudah dipahami, pastikan menyebutkan "karung" (1 karung = 50 kg) and "kg/ha".
3. Berikan estimasi peningkatan hasil panen jika petani mengikuti anjuran pupuk tersebut.
4. Urutkan (sort) daftar rekomendasi tanaman pada hasil akhir mulai dari yang memiliki **potensi hasil panen dan estimasi peningkatan paling tinggi** di urutan teratas, hingga yang terendah di bawah.
5. Gunakan bahasa yang SUPER SEDERHANA, merakyat, and mudah dipahami.

FORMAT OUTPUT — balas HANYA dengan JSON valid ini:
{
  "kondisi_ringkasan": "string (penjelasan singkat kondisi tanah)",
  "rekomendasi": [
    {
      "jenis_tanaman": "string",
      "alasan_cocok": "string",
      "estimasi_peningkatan": "string",
      "daftar_pupuk": [
        {
          "urutan": 1,
          "nama_pupuk": "string",
          "takaran_total": "string (contoh: 50 kg atau 1 karung)",
          "catatan": "string"
        }
      ]
    }
  ]
}"""

SYSTEM_PROMPT_SARAN_TANAMAN = """Kamu adalah Dr. Agro, ahli sistem pertanian cerdas. 
Tugasmu adalah merekomendasikan 3-4 jenis tanaman yang paling cocok ditanam berdasarkan data sensor tanah.

PRINSIP:
1. Analisis pH, N, P, dan K tanah.
2. Jelaskan MENGAPA tanaman tersebut cocok (hubungkan dengan data sensor).
3. Berikan contoh varietas yang populer di Indonesia.
4. Berikan catatan penting untuk pengelolaan tanah.

FORMAT OUTPUT — balas HANYA dengan JSON valid ini:
{
  "kondisi_dominan": "string (rangkuman kondisi hara tanah saat ini)",
  "rekomendasi": [
    {
      "nama": "string (Nama Tanaman)",
      "deskripsi": "string (Alasan mengapa cocok berdasarkan data sensor)",
      "contoh": ["string (Varietas 1)", "string (Varietas 2)"]
    }
  ],
  "catatan_penting": ["string (Saran perbaikan hara/tindakan petani)"]
}"""

def _bangun_konteks_riwayat(riwayat: list) -> str:
    if not riwayat: return ""
    baris = ["\n\n=== RIWAYAT DATA LAHAN ==="]
    for i, r in enumerate(riwayat, 1):
        baris.append(f"[#{i}] {r.get('jenis_tanaman')} | pH {r.get('ph_tanah')} | NPK {r.get('nitrogen')}/{r.get('fosfor')}/{r.get('kalium')}")
    baris.append("=== AKHIR RIWAYAT ===\n")
    return "\n".join(baris)

def _bersihkan_json(raw: str) -> str:
    if not raw: return "{}"
    text = raw.strip()
    
    # Remove markdown code blocks
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
        text = text.strip()
    
    # Try finding the first '{' or '[' and last '}' or ']'
    start_obj = text.find('{')
    start_arr = text.find('[')
    
    if start_obj != -1 and start_arr != -1:
        start = min(start_obj, start_arr)
    else:
        start = max(start_obj, start_arr)
        
    end_obj = text.rfind('}')
    end_arr = text.rfind(']')
    end = max(end_obj, end_arr)
    
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
        
    return text

async def generate_rekomendasi_pupuk(
    db, jenis_tanaman: str, fase_tumbuh: str, luas_lahan: float,
    ph: float, nitrogen: float, fosfor: float, kalium: float,
    suhu_udara: float = None, kelembaban_tanah: float = None,
    catatan_tambahan: str = None, status_tanah: dict = None, riwayat_lahan: list = None,
) -> dict:
    if os.getenv("USE_DUMMY_AI") == "true":
        return {"sukses": True, "is_dummy": True, "data": {"kondisi_ringkasan": "MODE DUMMY"}}

    profil = get_profil_tanaman(jenis_tanaman)
    prompt_lines = [
        f"=== DATA SENSOR: {jenis_tanaman.upper()} | {fase_tumbuh} | {luas_lahan} ha ===",
        f"pH: {ph} | N: {nitrogen} | P: {fosfor} | K: {kalium}",
        f"=== PROFIL IDEAL: pH {profil['ph_ideal']} | NPK {profil['n']}/{profil['p']}/{profil['k']}",
    ]
    if riwayat_lahan: prompt_lines.append(_bangun_konteks_riwayat(riwayat_lahan))
    
    dosis_manual = hitung_dosis_pupuk(db, jenis_tanaman, fase_tumbuh, luas_lahan, ph, nitrogen, fosfor, kalium, suhu=suhu_udara, kelembaban=kelembaban_tanah)
    if dosis_manual:
        prompt_lines.append("=== PERHITUNGAN DOSIS WAJIB ===")
        for d in dosis_manual: prompt_lines.append(f"- {d['nama']}: {d['kg']} kg ({d['karung']} karung)")

    if catatan_tambahan: prompt_lines.append(f"Catatan petani: {catatan_tambahan}")
    prompt = "\n".join(prompt_lines)

    last_error = None
    for model_name in MODELS_FALLBACK:
        try:
            logger.info(f"Mencoba model (Pupuk): {model_name}")
            
            if model_name.startswith("groq/"):
                if not groq_client: 
                    logger.warning("Groq client tidak terinisialisasi (API Key kosong?)")
                    continue
                m_real = model_name.split("/", 1)[1]
                response = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_PUPUK},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content
            else:
                response = await client.aio.models.generate_content(
                    model=model_name, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", system_instruction=SYSTEM_PROMPT_PUPUK, temperature=0.7)
                )
                text = response.text

            data = json.loads(_bersihkan_json(text))
            data["_model_used"] = model_name
            return {"sukses": True, "data": data}
        except Exception as e:
            logger.error(f"Gagal di model {model_name}: {e}")
            last_error = e
            if "API_KEY_INVALID" in str(e): return {"sukses": False, "status_code": 401, "error": "API Key tidak valid"}
            continue

    return {"sukses": False, "error": f"Semua model gagal: {last_error}"}

async def generate_saran_tanaman(ph: float, nitrogen: float, fosfor: float, kalium: float, suhu_udara: float = None, status_tanah: dict = None) -> dict:
    prompt = (
        f"=== DATA TANAH TERKINI ===\n"
        f"pH: {ph} | Nitrogen: {nitrogen} mg/kg | Fosfor: {fosfor} mg/kg | Kalium: {kalium} mg/kg\n"
        f"Suhu Udara: {suhu_udara or 'N/A'}°C\n"
    )
    last_error = None
    for model_name in MODELS_FALLBACK:
        try:
            logger.info(f"Mencoba model (Saran Tanaman): {model_name}")
            
            if model_name.startswith("groq/"):
                if not groq_client: continue
                m_real = model_name.split("/", 1)[1]
                response = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_SARAN_TANAMAN},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content
            else:
                response = await client.aio.models.generate_content(
                    model=model_name, 
                    contents=prompt, 
                    config=types.GenerateContentConfig(response_mime_type="application/json", system_instruction=SYSTEM_PROMPT_SARAN_TANAMAN, temperature=0.7)
                )
                text = response.text

            data = json.loads(_bersihkan_json(text))
            return {"sukses": True, "data": data}
        except Exception as e:
            logger.error(f"Gagal di model {model_name}: {e}")
            last_error = e
            continue
    return {"sukses": False, "error": f"Semua model gagal: {last_error}"}

async def generate_alur2_saran_tanaman_dan_pupuk(
    db, luas_lahan: float, ph: float, nitrogen: float, fosfor: float, kalium: float,
    suhu_udara: float = None, kelembaban_tanah: float = None, catatan_tambahan: str = None
) -> dict:
    # Step 1: Minta AI memilih tanaman yang cocok (sebanyak mungkin)
    prompt_step1 = (
        f"Berdasarkan data tanah: pH {ph}, N {nitrogen}, P {fosfor}, K {kalium}. "
        "Sebutkan SEBANYAK-BANYAKNYA jenis tanaman pertanian (padi, jagung, cabai, tomat, sayuran, palawija dll) yang SANGAT COCOK ditanam pada kondisi tanah tersebut tanpa batas. Berikan setidaknya 5-8 tanaman. "
        "Balas HANYA dengan JSON array berupa daftar string huruf kecil. Contoh: [\"jagung\", \"kedelai\", \"kacang hijau\", \"tomat\", \"cabai\"]."
    )
    
    crops = ["jagung", "kedelai", "cabai", "tomat", "kangkung"] # Fallback
    for model_name in MODELS_FALLBACK:
        try:
            if model_name.startswith("groq/"):
                if not groq_client: continue
                m_real = model_name.split("/", 1)[1]
                res1 = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[{"role": "user", "content": prompt_step1}],
                    temperature=0.4,
                    response_format={"type": "json_object"}
                )
                text1 = res1.choices[0].message.content
            else:
                res1 = await client.aio.models.generate_content(model=model_name, contents=prompt_step1, config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4))
                text1 = res1.text
            
            parsed = json.loads(_bersihkan_json(text1))
            if isinstance(parsed, list) and len(parsed) > 0:
                crops = parsed
                break
            elif isinstance(parsed, dict) and "tanaman" in parsed:
                crops = parsed["tanaman"]
                break
        except Exception:
            pass

    # Step 2: Hitung dosis dengan Rule Engine untuk setiap tanaman
    hasil_perhitungan = []
    for crop in crops:
        dosis = hitung_dosis_pupuk(db, crop, "Total", luas_lahan, ph, nitrogen, fosfor, kalium, suhu_udara, kelembaban_tanah)
        hasil_perhitungan.append({
            "tanaman": crop,
            "dosis": dosis
        })

    # Step 3: Minta AI merangkum perhitungan tersebut
    prompt_lines = [
        f"=== DATA SENSOR: Luas Lahan {luas_lahan} ha ===",
        f"pH: {ph} | N: {nitrogen} | P: {fosfor} | K: {kalium}",
    ]
    if catatan_tambahan: prompt_lines.append(f"Catatan petani: {catatan_tambahan}")
    
    prompt_lines.append("=== PERHITUNGAN DOSIS DARI RULE ENGINE ===")
    prompt_lines.append(json.dumps(hasil_perhitungan, indent=2))
    
    prompt_step3 = "\n".join(prompt_lines)

    last_error = None
    for model_name in MODELS_FALLBACK:
        try:
            logger.info(f"Mencoba model Alur 2: {model_name}")
            
            if model_name.startswith("groq/"):
                if not groq_client: continue
                m_real = model_name.split("/", 1)[1]
                response = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_ALUR2},
                        {"role": "user", "content": prompt_step3}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                text3 = response.choices[0].message.content
            else:
                response = await client.aio.models.generate_content(
                    model=model_name, contents=prompt_step3,
                    config=types.GenerateContentConfig(response_mime_type="application/json", system_instruction=SYSTEM_PROMPT_ALUR2, temperature=0.7)
                )
                text3 = response.text

            data = json.loads(_bersihkan_json(text3))
            data["_model_used"] = model_name
            return {"sukses": True, "data": data}
        except Exception as e:
            logger.error(f"Gagal di model {model_name}: {e}")
            last_error = e
            if "API_KEY_INVALID" in str(e): return {"sukses": False, "status_code": 401, "error": "API Key tidak valid"}
            continue

    return {"sukses": False, "error": f"Semua model gagal memproses Alur 2: {last_error}"}