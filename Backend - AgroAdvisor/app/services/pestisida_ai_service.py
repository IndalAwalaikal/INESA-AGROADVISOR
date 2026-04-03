import os
import json
import httpx
from google import genai
from google.genai import types
from groq import AsyncGroq
from app.services.rule_engine import hitung_dosis_pestisida
from app.services.db_service import get_hama_penyakit
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_key = os.getenv("GROQ_API_KEY")
groq_client = AsyncGroq(api_key=groq_key) if groq_key else None

# Ollama config (fallback terakhir)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Daftar model untuk fallback (berurutan dari prioritas tertinggi)
MODELS_FALLBACK = [
    'gemini-2.5-flash-lite', 
    'gemini-2.5-flash', 
    'gemini-flash-latest',
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite',
    'groq/llama-3.3-70b-versatile',
    f'ollama/{OLLAMA_MODEL}',
]

async def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Panggil Ollama via OpenAI-compatible API. Fallback terakhir."""
    async with httpx.AsyncClient(timeout=120.0) as http:
        response = await http.post(
            f"{OLLAMA_BASE_URL}/v1/chat/completions",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

# ─── Profil Hama & Penyakit Per Tanaman ──────────────────────────────────────
PROFIL_HAMA = {
    "padi": {
        "hama_umum": [
            "Wereng coklat (Nilaparvata lugens)",
            "Penggerek batang (Scirpophaga incertulas)",
            "Tikus sawah (Rattus argentiventer)",
            "Walang sangit (Leptocorisa oratorius)",
            "Ulat grayak (Spodoptera frugiperda)",
        ],
        "penyakit_umum": [
            "Blas (Pyricularia oryzae)",
            "Hawar daun bakteri / kresek (Xanthomonas oryzae)",
            "Busuk batang (Helminthosporium)",
            "Tungro (Rice tungro virus)",
        ],
        "gulma_umum": [
            "Eceng gondok / gulma air",
            "Rumput belulang (Eleusine indica)",
            "Teki ladang (Cyperus rotundus)",
            "Bayam duri (Amaranthus spinosus)",
            "Gulma berdaun lebar sawah",
        ],
        "catatan": "Perhatikan PHI — padi biasanya dipanen 90-120 HST. Hindari insektisida saat berbunga. Herbisida pra-tumbuh hanya digunakan sebelum tanam.",
    },
    "jagung": {
        "hama_umum": [
            "Ulat penggerek batang (Ostrinia furnacalis)",
            "Ulat grayak (Spodoptera frugiperda)",
            "Aphid jagung (Rhopalosiphum maidis)",
            "Kumbang bubuk (Sitophilus zeamais)",
        ],
        "penyakit_umum": [
            "Bule jagung (Peronosclerospora maydis)",
            "Hawar daun (Helminthosporium turcicum)",
            "Busuk tongkol (Fusarium moniliforme)",
            "Karat daun (Puccinia sorghi)",
        ],
        "gulma_umum": [
            "Rumput belulang (Eleusine indica)",
            "Teki ladang (Cyperus rotundus)",
            "Alang-alang (Imperata cylindrica)",
            "Putri malu (Mimosa pudica)",
        ],
        "catatan": "Ulat grayak (FAW) sangat merusak — prioritas pengendalian dini. Alang-alang sangat kompetitif, gunakan herbisida sistemik.",
    },
    "cabai": {
        "hama_umum": [
            "Thrips (Thrips parvispinus)",
            "Kutu daun / Aphid (Myzus persicae)",
            "Tungau merah (Tetranychus urticae)",
            "Lalat buah (Bactrocera dorsalis)",
            "Ulat buah (Helicoverpa armigera)",
        ],
        "penyakit_umum": [
            "Antraknosa / patek (Colletotrichum capsici)",
            "Layu fusarium (Fusarium oxysporum)",
            "Virus kuning / gemini virus",
            "Busuk buah (Phytophthora capsici)",
            "Bercak daun (Cercospora capsici)",
        ],
        "gulma_umum": [
            "Rumput belulang (Eleusine indica)",
            "Bayam liar (Amaranthus spp.)",
            "Teki ladang (Cyperus rotundus)",
        ],
        "catatan": "Thrips dan virus kuning sering berkaitan — kendalikan thrips untuk cegah virus. Gulma bisa jadi inang thrips.",
    },
    "tomat": {
        "hama_umum": [
            "Kutu kebul (Bemisia tabaci)",
            "Thrips (Thrips palmi)",
            "Ulat buah (Helicoverpa armigera)",
            "Tungau merah (Tetranychus urticae)",
            "Nematoda (Meloidogyne spp.)",
        ],
        "penyakit_umum": [
            "Layu bakteri (Ralstonia solanacearum)",
            "Bercak coklat (Alternaria solani)",
            "Busuk buah (Phytophthora infestans)",
            "Virus mozaik tomat (ToMV)",
            "Keriting daun (TYLCV)",
        ],
        "gulma_umum": [
            "Rumput belulang (Eleusine indica)",
            "Bayam liar",
            "Teki ladang (Cyperus rotundus)",
        ],
        "catatan": "Rotasi tanaman penting untuk cegah layu bakteri yang persisten di tanah. Gulma bisa jadi inang kutu kebul.",
    },
    "kedelai": {
        "hama_umum": [
            "Pengisap polong (Riptortus linearis)",
            "Ulat grayak (Spodoptera litura)",
            "Lalat kacang (Agromyza phaseoli)",
            "Kutu daun (Aphis glycines)",
        ],
        "penyakit_umum": [
            "Karat kedelai (Phakopsora pachyrhizi)",
            "Sclerotinia / busuk batang putih",
            "Mosaik kedelai (SMV)",
            "Busuk polong (Phomopsis sojae)",
        ],
        "gulma_umum": [
            "Teki ladang (Cyperus rotundus)",
            "Rumput belulang (Eleusine indica)",
            "Gulma berdaun lebar umum",
        ],
        "catatan": "Karat kedelai bisa menyebabkan gagal panen — semprot fungisida preventif jika musim hujan.",
    },
    "singkong": {
        "hama_umum": [
            "Tungau merah singkong (Tetranychus cinnabarinus)",
            "Kutu putih (Phenacoccus manihoti)",
            "Penggerek batang (Chilades pandava)",
        ],
        "penyakit_umum": [
            "Layu bakteri (Xanthomonas campestris)",
            "Bercak coklat (Cercospora henningsii)",
            "Busuk umbi (Phytophthora drechsleri)",
        ],
        "gulma_umum": [
            "Alang-alang (Imperata cylindrica)",
            "Rumput belulang (Eleusine indica)",
            "Teki ladang (Cyperus rotundus)",
        ],
        "catatan": "Singkong relatif tahan hama, fokus pada tungau merah di musim kemarau. Alang-alang sangat kompetitif di awal tanam.",
    },
}


def get_profil_hama(jenis_tanaman: str) -> dict:
    """Ambil profil hama untuk tanaman. Kembalikan generik jika tidak dikenal."""
    kunci = jenis_tanaman.lower().strip()
    return PROFIL_HAMA.get(kunci, {
        "hama_umum":     ["Aphid", "Ulat", "Tungau", "Thrips"],
        "penyakit_umum": ["Jamur daun", "Layu", "Bercak daun"],
        "catatan":       f"Gunakan panduan umum pengendalian hama untuk {jenis_tanaman}.",
    })


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_PESTISIDA = """Kamu adalah Dr. Proteksi, ahli perlindungan tanaman (plant protection) \
berpengalaman 20 tahun di Indonesia, spesialis pengendalian hama, penyakit, DAN gulma tanaman.

CARA KERJAMU:
1. Tentukan apakah masalahnya adalah HAMA HEWANI (serangga, tungau, tikus), PENYAKIT (jamur, bakteri, virus), atau GULMA/RUMPUT LIAR
2. Untuk gulma: bedakan antara rumput (monocot), teki-tekian, dan gulma berdaun lebar (dicot) — karena herbisidanya berbeda
3. Tentukan strategi pengendalian yang tepat: kimia, biologi, atau kombinasi
4. Rekomendasikan pestisida/herbisida yang sesuai dengan merek yang tersedia di Indonesia
5. Hitung dosis berdasarkan luas lahan
6. Berikan jadwal, interval, dan waktu aplikasi terbaik
7. Selalu sertakan PHI dan peringatan keamanan

PRINSIP REKOMENDASI:
- Gunakan prinsip PHT (Pengendalian Hama Terpadu): dahulukan cara non-kimia jika memungkinkan
- WAJIB prioritaskan produk yang SANGAT DIKENAL dan MUDAH DIBELI petani di kios/toko pertanian desa. \
  Utamakan produk bersubsidi pemerintah atau yang paling umum:
  * INSEKTISIDA (hama serangga): Regent 50SC (Fipronil), Furadan 3G (Karbofuran, utk nematoda/penggerek), \
    Dursban (Klorpirifos), Curacron (Profenofos), Decis (Deltametrin), Prevathon (Klorantraniliprol), \
    Virtako (Tiametoksam+Klorantraniliprol), Buldok (Beta-siflutrin)
  * FUNGISIDA (penyakit jamur): Antracol (Propineb), Dithane M-45 (Mankozeb), Score (Difenokonazol), \
    Amistartop (Azoksistrobin), Daconil (Klorotalonil), Nordox (Oksida tembaga)
  * HERBISIDA — sesuaikan jenis gulma:
    > Rumput belulang & alang-alang → Gramoxone 276SL (Paraquat), Roundup 486SL (Glifosat), DMA-6 (2,4-D amin)
    > Teki ladang (Cyperus) → Basagran 500SL (Bentazon) khusus teki, Saturn B (Tiobenkarb)
    > Gulma sawah campuran → Nominee 100SC (Bispyribac-sodium), Londax 60DF (Bensulfuron), Stam M-4
    > Gulma berdaun lebar → DMA-6 (2,4-D amin), Lodon 48EC
    > Sebelum tanam (pra-tumbuh) → Dual Gold 960EC (Metolakhlor), Lasso (Alaklor)
- Berikan alternatif organik/biologi sebagai pilihan
- Sesuaikan dosis dengan tingkat serangan: ringan = dosis bawah, berat = dosis atas
- Pertimbangkan kondisi cuaca: jangan semprot saat hujan atau angin kencang, semprot pagi/sore
- SELALU sertakan PHI — terutama penting untuk sayuran dan buah
- Sebutkan dosis dalam satuan PRAKTIS sesuai hasil PERHITUNGAN DOSIS yang diberikan dalam prompt (WAJIB DIGUNAKAN).
- Gunakan bahasa SEDERHANA, sehari-hari, dan mudah dimengerti petani desa

FORMAT OUTPUT — balas HANYA dengan JSON valid ini, tanpa teks di luar JSON:
{
  "identifikasi": {
    "nama_hama": "string",
    "jenis_organisme": "serangga | jamur | bakteri | virus | tungau | nematoda | gulma_rumput | gulma_teki | gulma_berdaun_lebar | gulma_campuran | gulma_air",
    "tingkat_serangan": "ringan | sedang | berat",
    "deskripsi_gejala": "string",
    "potensi_kerugian": "string"
  },
  "strategi_pengendalian": "string",
  "daftar_pestisida": [
    {
      "urutan": 1,
      "nama_pestisida": "string",
      "bahan_aktif": "string",
      "jenis_pestisida": "string",
      "dosis_per_liter_air": "string",
      "dosis_per_ha": "string",
      "dosis_total": "string",
      "waktu_semprot": "string",
      "interval_semprot": "string",
      "metode_aplikasi": "string",
      "phi": "string",
      "tujuan": "string",
      "urutan_aplikasi": "string"
    }
  ],
  "kombinasi_diizinkan": ["string"],
  "kombinasi_dilarang": ["string"],
  "alternatif_organik": [
    {
      "nama": "string",
      "cara_pakai": "string",
      "efektivitas": "string"
    }
  ],
  "jadwal_pengendalian": "string",
  "estimasi_efektivitas": "string",
  "tanda_berhasil": "string",
  "catatan_keamanan": "string",
  "peringatan": ["string"]
}"""


def _bersihkan_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                return part
    return text


def _bangun_konteks_riwayat_hama(riwayat: list) -> str:
    """Bangun konteks riwayat penanganan hama sebelumnya untuk pembelajaran AI."""
    if not riwayat:
        return ""
    baris = ["\n\n=== RIWAYAT PENANGANAN HAMA SEBELUMNYA ==="]
    for i, r in enumerate(riwayat, 1):
        baris.append(f"[#{i} — {r.get('tanggal', '-')}] {r.get('jenis_hama')} ({r.get('tingkat_serangan')})")
    baris.append("=== AKHIR RIWAYAT ===\n")
    return "\n".join(baris)


async def generate_rekomendasi_pestisida(
    db,               # SQLAlchemy session
    jenis_tanaman:    str,
    jenis_hama:       str,
    tingkat_serangan: str,
    luas_lahan:       float,
    usia_tanaman:     str        = None,
    kondisi_cuaca:    str        = None,
    riwayat_pestisida: str       = None,
    catatan_tambahan: str        = None,
    suhu_udara:       float      = None,
    hujan_terdeteksi: bool       = False,
    riwayat_lahan:    list       = None,
) -> dict:
    if os.getenv("USE_DUMMY_AI") == "true":
        return {"sukses": True, "is_dummy": True, "data": {"identifikasi": {"nama_hama": jenis_hama}}}

    # Ambil data dari database (Master Data Hama/Penyakit)
    db_pests = get_hama_penyakit(db, jenis_tanaman)
    fixed_profil = get_profil_hama(jenis_tanaman)
    
    context_pests = []
    if db_pests:
        for p in db_pests:
            context_pests.append(f"- {p['nama_umum']} ({p['nama_ilmiah']}): {p['gejala_utama']}")
    else:
        context_pests.append(f"- Hama Umum: {', '.join(fixed_profil['hama_umum'])}")

    if not kondisi_cuaca:
        if hujan_terdeteksi: kondisi_cuaca = "hujan / lembab"
        elif suhu_udara and suhu_udara > 33: kondisi_cuaca = "panas terik"
        else: kondisi_cuaca = "normal"

    prompt_lines = [
        f"=== DATA SERANGAN: {jenis_tanaman.upper()} | {jenis_hama} ({tingkat_serangan}) | {luas_lahan} ha ===",
        f"Cuaca: {kondisi_cuaca} | Suhu: {suhu_udara}°C",
    ]

    if riwayat_lama := _bangun_konteks_riwayat_hama(riwayat_lahan):
        prompt_lines.append(riwayat_lama)

    # --- HITUNG DOSIS DENGAN RULE ENGINE ---
    dosis_manual = hitung_dosis_pestisida(jenis_hama, luas_lahan, tingkat_serangan, jenis_tanaman=jenis_tanaman, usia=usia_tanaman)
    if dosis_manual:
        prompt_lines.append("=== PERHITUNGAN DOSIS WAJIB ===")
        prompt_lines.append(f"- Konsentrasi: {dosis_manual['ml_per_liter']} ml/liter")
        prompt_lines.append(f"- Total Air: {dosis_manual['total_air_liter']} liter")
        prompt_lines.append(f"- Total Pestisida: {dosis_manual['total_pestisida_ml']} ml")

    if catatan_tambahan: prompt_lines.append(f"Catatan petani: {catatan_tambahan}")
    prompt = "\n".join(prompt_lines)

    last_error = None
    for model_name in MODELS_FALLBACK:
        try:
            import logging
            logging.info(f"Mencoba model: {model_name}")
            
            if model_name.startswith("ollama/"):
                text = await _call_ollama(SYSTEM_PROMPT_PESTISIDA, prompt)
            elif model_name.startswith("groq/"):
                if not groq_client: continue
                m_real = model_name.split("/", 1)[1]
                response = await groq_client.chat.completions.create(
                    model=m_real,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_PESTISIDA},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content
            else:
                response = client.models.generate_content(
                    model=model_name, contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT_PESTISIDA, temperature=0.7)
                )
                text = response.text
            
            data = json.loads(_bersihkan_json(text))
            data["_model_used"] = model_name
            return {"sukses": True, "data": data}
        except Exception as e:
            last_error = e
            continue

    return {"sukses": False, "error": f"Semua model gagal: {last_error}"}


# ─── System Prompt untuk Identifikasi Gambar ──────────────────────────────────

SYSTEM_PROMPT_VISION = """Kamu adalah ahli agronomi dan patologi tumbuhan.
Tugasmu adalah mengidentifikasi jenis hama, penyakit, atau gulma dari gambar yang diberikan.
Jawab dengan nama umum hama/penyakit yang paling mungkin terlihat di gambar.
Jika gambarnya tidak jelas, tebak yang paling relevan dengan pertanian.

Keluarkan HANYA JSON dengan format berikut, tanpa penjelasan tambahan:
{
  "nama_hama": "Wereng Coklat"
}"""

async def identifikasi_hama_dari_gambar(image_bytes: bytes, mime_type: str) -> dict:
    if os.getenv("USE_DUMMY_AI") == "true":
        return {"sukses": True, "nama_hama": "Wereng Coklat (Dummy)"}

    try:
        # Menggunakan model flash yang mendukung visi
        import logging
        logging.info("Menganalisis gambar hama dengan Gemini...")
        
        # Format payload untuk gambar
        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": image_bytes
            }
        }
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[SYSTEM_PROMPT_VISION, image_part],
            config=types.GenerateContentConfig(temperature=0.2)
        )
        
        data = json.loads(_bersihkan_json(response.text))
        nama_hama = data.get("nama_hama", "Hama tidak teridentifikasi")
        
        return {
            "sukses": True, 
            "nama_hama": nama_hama
        }
    except Exception as e:
        return {"sukses": False, "error": f"Gagal menganalisis gambar: {str(e)}"}