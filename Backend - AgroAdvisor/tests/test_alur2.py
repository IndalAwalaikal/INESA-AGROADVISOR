import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_alur_2_recommendation():
    payload = {
        "luas_lahan": 1.0,
        "gunakan_sensor_live": False,
        "data_sensor": {
            "ph_tanah": 6.5,
            "nitrogen": 120,
            "fosfor": 40,
            "kalium": 100,
            "suhu_udara": 28.0,
            "kelembaban_tanah": 60.0
        }
    }
    
    response = client.post("/api/pupuk/alur2-saran", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["sukses"] is True
    assert "saran_alur2" in data
    assert "kondisi_tanah" in data
    
    alur2 = data["saran_alur2"]
    assert "rekomendasi" in alur2
    assert isinstance(alur2["rekomendasi"], list)
