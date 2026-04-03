from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Request Models ───────────────────────────────────────────────────────────

class DataSensorInput(BaseModel):
    """Data sensor tanah — digunakan saat input manual (bukan dari file JSON)."""
    ph_tanah:          float           = Field(..., ge=0,    le=14)
    nitrogen:          float           = Field(..., ge=0)
    fosfor:            float           = Field(..., ge=0)
    kalium:            float           = Field(..., ge=0)
    suhu_udara:        Optional[float] = None
    kelembaban_udara:  Optional[float] = None
    kelembaban_tanah:  Optional[float] = None
    hujan_terdeteksi:  Optional[bool]  = False


class RekomendasiPupukRequest(BaseModel):
    """Request rekomendasi pupuk dari user/dashboard frontend (Alur 1)."""
    jenis_tanaman:       str            = Field(...,    description="Contoh: padi, jagung, cabai, tomat")
    fase_tumbuh:         str            = Field("vegetatif", description="bibit | vegetatif | generatif | panen")
    luas_lahan:          float          = Field(1.0,    ge=0.01, description="Luas lahan dalam hektar")
    lokasi:              Optional[str]  = None
    catatan_tambahan:    Optional[str]  = None
    gunakan_sensor_live: bool           = Field(True,   description="True = baca file JSON IoT | False = pakai data_sensor manual")
    data_sensor:         Optional[DataSensorInput] = None


class Alur2SaranTanamanDanPupukRequest(BaseModel):
    """Request rekomendasi 2-3 tanaman sekaligus dosis pupuk berdasarkan tanah (Alur 2)."""
    luas_lahan:          float          = Field(1.0, ge=0.01, description="Luas lahan dalam hektar")
    lokasi:              Optional[str]  = None
    catatan_tambahan:    Optional[str]  = None
    gunakan_sensor_live: bool           = Field(True, description="True = baca dari JSON IoT | False = pakai data_sensor manual")
    data_sensor:         Optional[DataSensorInput] = None



class ResetSesiRequest(BaseModel):
    """Request reset sesi pengujian tanah."""
    catatan_reset: Optional[str] = None
    lokasi_baru:   Optional[str] = None


class FeedbackRequest(BaseModel):
    """Feedback dari petani setelah mengaplikasikan pupuk."""
    rekomendasi_id: int
    rating:         int            = Field(..., ge=1, le=5, description="Rating 1–5")
    catatan_hasil:  Optional[str]  = None


# ─── Response Models ──────────────────────────────────────────────────────────

class StatusSensor(BaseModel):
    """Status data sensor terkini beserta evaluasi tiap parameter."""
    device_id:          str
    lokasi:             str
    sesi_id:            str
    timestamp:          str
    ph_tanah:           float
    nitrogen:           float
    fosfor:             float
    kalium:             float
    suhu_udara:         Optional[float]
    kelembaban_udara:   Optional[float]
    kelembaban_tanah:   Optional[float]
    hujan_terdeteksi:   bool
    status_ph:          str
    status_nitrogen:    str
    status_fosfor:      str
    status_kalium:      str