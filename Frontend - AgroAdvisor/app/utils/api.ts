import axios from 'axios';

const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const port = window.location.port;
    // Jika diakses melalui Nginx (port 80/8080/kosong), gunakan relative URL
    if (port === '' || port === '80' || port === '8080' || port === '443') {
      return '';
    }
    // Development mode — langsung ke backend
    return `http://${window.location.hostname}:8001`;
  }
  return 'http://localhost:8001';
};

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
});

// ── Pupuk ────────────────────────────────────────────────────────────────────
export const getSensorStatus   = () => api.get('/api/pupuk/sensor/status');
export const getSaranTanaman   = () => api.get('/api/pupuk/saran-tanaman');
export const getDaftarTanaman  = () => api.get('/api/pupuk/tanaman/daftar');
export const postRekomendasiPupuk = (data: any) => api.post('/api/pupuk/rekomendasi', data);
export const postAlur2Saran    = (data: any) => api.post('/api/pupuk/alur2-saran', data);
export const postFeedback      = (data: any) => api.post('/api/pupuk/feedback', data);
export const postResetSesi     = (data: any) => api.post('/api/pupuk/reset-sesi', data);
export const getRiwayatPupuk   = (page = 1, limit = 20) => api.get(`/api/pupuk/riwayat?page=${page}&limit=${limit}`);
export const getStatistik      = () => api.get('/api/pupuk/statistik');
export const getPupukPDF       = (id: string | number) => `${api.defaults.baseURL}/api/pupuk/rekomendasi/${id}/pdf`;

// ── Pestisida ────────────────────────────────────────────────────────────────
export const postRekomendasiPestisida = (data: any) => api.post('/api/pestisida/rekomendasi', data);
export const getDaftarHama     = (tanaman?: string) => api.get(`/api/pestisida/hama/daftar${tanaman ? `?tanaman=${tanaman}` : ''}`);
export const getRiwayatPestisida = (page = 1, limit = 20) => api.get(`/api/pestisida/riwayat?page=${page}&limit=${limit}`);
export const postPestisidaFeedback = (data: any) => api.post('/api/pestisida/feedback', data);
export const getPestisidaPDF   = (id: string | number) => `${api.defaults.baseURL}/api/pestisida/rekomendasi/${id}/pdf`;

export const getStatusPompa    = () => api.get('/api/pompa/status');
export const postKontrolPompa  = (status: 'on' | 'off') => api.post('/api/pompa/manual', { perintah: status === 'on' ? 'nyala' : 'mati' });
export const getConfigPompa    = () => api.get('/api/pompa/konfigurasi');
export const postUpdateConfigPompa = (data: any) => api.put('/api/pompa/konfigurasi', data);
export const getRiwayatPompa   = (page = 1, limit = 30) => api.get(`/api/pompa/riwayat?page=${page}&limit=${limit}`);

// ── Jadwal Pompa ──────────────────────────────────────────────────────────────
export const getJadwalPompa       = () => api.get('/api/pompa/jadwal');
export const postJadwalPompa      = (data: { jam: string; durasi_menit: number; hari?: string }) => api.post('/api/pompa/jadwal', data);
export const deleteJadwalPompa    = (id: number) => api.delete(`/api/pompa/jadwal/${id}`);
export const toggleJadwalPompa    = (id: number, aktif: boolean) => api.put(`/api/pompa/jadwal/${id}/toggle`, { aktif });

// ── Ekspor CSV ────────────────────────────────────────────────────────────────
export const getExportPupukCSV     = () => `${api.defaults.baseURL}/api/pupuk/riwayat/export/csv`;
export const getExportPestisidaCSV = () => `${api.defaults.baseURL}/api/pestisida/riwayat/export/csv`;
export const getExportPompaCSV     = () => `${api.defaults.baseURL}/api/pompa/riwayat/export/csv`;

// ── Cuaca ─────────────────────────────────────────────────────────────────────
export const getCuacaSekarang  = () => api.get('/api/cuaca/sekarang');
export const getPrakiraanCuaca = () => api.get('/api/cuaca/prakiraan');
export const getHujanAlert     = () => api.get('/api/cuaca/hujan-alert');

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboard      = () => api.get('/dashboard');
