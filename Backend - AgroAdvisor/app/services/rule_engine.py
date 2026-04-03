"""
Rule Engine for AgriSmart - Specialized for Indonesian Agronomic Standards.
This module provides deterministic calculations based on standards from Kementan/Balitbangtan.
Data is fetched from the 'kebutuhan_hara' database table.
"""
from app.services.db_service import get_kebutuhan_hara

def hitung_dosis_pupuk(db, jenis_tanaman, fase, luas, ph, n, p, k, suhu=None, kelembaban=None):
    """
    Detailed agronomic calculation using a 'Nutrient Gap' approach.
    Now considers pH correction, environmental factors, and subsidized fertilizer types.
    """
    # 1. Fetch Crop Profile from DB
    crop = get_kebutuhan_hara(db, jenis_tanaman)
    if not crop:
        # Fallback to a generic profile if not found
        crop = {
            "nama": jenis_tanaman,
            "n_req": 120, "p_req": 60, "k_req": 60,
            "ph_min": 5.5, "ph_max": 7.0,
            "kebutuhan_air": "Medium"
        }

    rekomendasi = []

    # 2. pH Correction (Kapur Pertanian / Dolomit)
    if ph < crop["ph_min"]:
        deficit = crop["ph_min"] - ph
        kapur_kg = (deficit / 0.5) * 1000 * luas # 1 ton = 1000kg per 0.5 pH deficit
        if kapur_kg > 10:
             rekomendasi.append({
                "nama": "Kapur Pertanian (Dolomit/Gamping)",
                "kg": round(kapur_kg, 1),
                "karung": round(kapur_kg / 50, 1),
                "catatan": f"pH tanah {ph} terlalu asam (Ideal: {crop['ph_min']}-{crop['ph_max']}). Taburkan kapur untuk menetralkan."
            })

    # 3. Phase Multiplier (Split application strategy)
    phase_map = {
        "Minggu 1-2": 0.3, # Dasar / Starter (30%)
        "Minggu 3-4": 0.35, # Susulan 1 (35%)
        "Minggu 5-6": 0.35, # Susulan 2 (35%)
        "Minggu 7-10": 0.1, # Maintenance
        "Minggu 13+": 0.0, # Panen
        "Total": 1.0, # Alur 2: Rekomendasi total semusim
        "Semua Fase": 1.0 # Alternatif
    }
    
    mult = 0.3 # Default
    for key, val in phase_map.items():
        if key.lower() in fase.lower():
            mult = val
            break

    # 4. Nutrient Gap Calculation
    # Target per hectare for this phase
    target_n = crop["n_req"] * mult
    target_p = crop["p_req"] * mult
    target_k = crop["k_req"] * mult

    # Sensor Adjustment (Scale 0-300 mg/kg)
    def get_gap_mult(val, low=80, mid=150):
        if val < low: return 1.2 # Soil is poor, increase dose 20%
        if val > mid: return 0.6 # Soil is rich, reduce dose 40%
        return 1.0

    adj_n = get_gap_mult(n)
    adj_p = get_gap_mult(p, 20, 50)
    adj_k = get_gap_mult(k)

    target_n *= adj_n
    target_p *= adj_p
    target_k *= adj_k

    # 5. Environmental Factors
    if suhu and suhu > 33:
        target_n *= 1.1 # Nitrogen leaches faster in heat

    # 6. Fertilizer Allocation (Priority: Subsidized & Common)
    # Fertilizers:
    # - NPK Phonska (15-15-15) -> 15% N, 15% P2O5, 15% K2O
    # - Urea (46% N)
    # - ZA (21% N) -> Higher Sulfur
    # - SP-36 (36% P2O5)
    # - KCl (60% K2O)
    # - ZK (50% K2O) -> Higher Sulfur

    rem_n = target_n
    rem_p = target_p
    rem_k = target_k

    # Strategy: Use NPK Phonska as the base to fulfill P requirement
    p_phonska = target_p / 0.15
    kg_phonska = p_phonska * luas
    if kg_phonska > 1:
        rekomendasi.append({
            "nama": "Pupuk NPK Phonska (15-15-15)",
            "kg": round(kg_phonska, 1),
            "karung": round(kg_phonska / 50, 1),
            "catatan": "Pupuk majemuk subsidi, penuhi kebutuhan NPK dasar."
        })
        # Subtract nutrients provided by Phonska
        rem_n -= p_phonska * 0.15
        rem_p -= p_phonska * 0.15
        rem_k -= p_phonska * 0.15

    # Fill remaining Nitrogen gap with Urea or ZA
    if rem_n > 5:
        # Prioritize Urea for general use, ZA if crop likes Sulfur (e.g. Bawang, Cabai)
        is_sulfur_crop = any(x in jenis_tanaman.lower() for x in ["bawang", "cabai", "tomat", "padi"])
        if is_sulfur_crop:
            kg_za = (rem_n / 0.21) * luas
            rekomendasi.append({
                "nama": "Pupuk ZA (21% N, 24% S)",
                "kg": round(kg_za, 1),
                "karung": round(kg_za / 50, 1),
                "catatan": "Sumber Nitrogen + Sulfur untuk kuantitas & aroma hasil panen."
            })
        else:
            kg_urea = (rem_n / 0.46) * luas
            rekomendasi.append({
                "nama": "Pupuk Urea (46% N)",
                "kg": round(kg_urea, 1),
                "karung": round(kg_urea / 50, 1),
                "catatan": "Pupuk Nitrogen subsidi untuk pertumbuhan vegetatif cepat."
            })

    # Fill remaining Phosphorus gap (if Phonska wasn't enough)
    if rem_p > 2:
        kg_sp36 = (rem_p / 0.36) * luas
        rekomendasi.append({
            "nama": "Pupuk SP-36 (36% P2O5)",
            "kg": round(kg_sp36, 1),
            "karung": round(kg_sp36 / 50, 1),
            "catatan": "Tambahan Fosfor untuk penguatan akar dan batang."
        })

    # Fill remaining Potassium gap with KCl or ZK
    if rem_k > 5:
        # ZK is better for tobacco, onion, potato (low chlorine crops)
        is_low_chlorine = any(x in jenis_tanaman.lower() for x in ["tembakau", "bawang", "kentang", "cabai"])
        if is_low_chlorine:
            kg_zk = (rem_k / 0.50) * luas
            rekomendasi.append({
                "nama": "Pupuk ZK (50% K2O, 18% S)",
                "kg": round(kg_zk, 1),
                "karung": round(kg_zk / 50, 1),
                "catatan": "Pupuk Kalium bebas Klorin, bagus untuk kualitas buah/umbi."
            })
        else:
            kg_kcl = (rem_k / 0.60) * luas
            rekomendasi.append({
                "nama": "Pupuk KCl (60% K2O)",
                "kg": round(kg_kcl, 1),
                "karung": round(kg_kcl / 50, 1),
                "catatan": "Sumber Kalium tinggi untuk ketahanan tanaman & bobot hasil."
            })

    return rekomendasi

def hitung_dosis_pestisida(hama, luas, tingkat, jenis_tanaman="padi", usia="Minggu 1-2"):
    """
    Pesticide volume varies based on canopy size (crop age) and area.
    """
    # Base concentration (ml/L)
    tingkat_map = {"ringan": 1.0, "sedang": 2.0, "berat": 3.5}
    ml_per_liter = tingkat_map.get(tingkat.lower(), 2.0)
    
    # Volume semprot (Spraying Volume) per Ha based on crop age/canopy
    # Young crops need less water (tank sprayers reach everything easily)
    base_vol = 400 # Default 400L/Ha
    if "Minggu 1-4" in usia or "Minggu 1-2" in usia:
        base_vol = 250 # Canopy small
    elif "Minggu 9" in usia or "Minggu 13" in usia:
        base_vol = 500 # Full canopy
        
    total_air = base_vol * luas
    total_ml = ml_per_liter * total_air
    
    return {
        "ml_per_liter": ml_per_liter,
        "total_air_liter": round(total_air, 1),
        "total_pestisida_ml": round(total_ml, 0),
        "tutup_botol": round(total_ml / 10, 1),
        "asumsi_tangki": round(total_air / 15, 1), # average 15L tank
        "catatan": f"Gunakan volume semprot {base_vol} L/Ha karena tanaman di fase {usia}."
    }
