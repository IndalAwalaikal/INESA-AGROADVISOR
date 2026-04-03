const axios = require('axios');

async function test() {
  try {
    const res = await axios.post('http://localhost:8001/api/pupuk/alur2-saran', {
      luas_lahan: 1, // 1 Ha
      catatan_tambahan: "test",
      gunakan_sensor_live: true
    });
    console.log("Alur 2 Response keys:", Object.keys(res.data));
    console.log("Saran Alur 2 keys:", Object.keys(res.data.saran_alur2));
    if (res.data.saran_alur2.rekomendasi.length > 0) {
       console.log("Rekomendasi keys:", Object.keys(res.data.saran_alur2.rekomendasi[0]));
    }
    
    // Test Alur 1
    const res1 = await axios.post('http://localhost:8001/api/pupuk/rekomendasi', {
       jenis_tanaman: "padi",
       fase_tumbuh: "Minggu 3-4 (pertumbuhan awal)",
       luas_lahan: 1,
       gunakan_sensor_live: true
    })
    console.log("\nAlur 1 Response keys:", Object.keys(res1.data));
    if (res1.data.daftar_pupuk) {
       console.log("Daftar pupuk:", res1.data.daftar_pupuk[0]);
    }
  } catch (err) {
    console.error("Error:", err.response?.data || err.message);
  }
}

test();
