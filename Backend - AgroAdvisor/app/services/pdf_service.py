from fpdf import FPDF
from datetime import datetime
import json

def safe_text(text):
    if text is None:
        return "-"
    # Convert to string and handle non-latin-1 characters
    s = str(text)
    return s.encode("latin-1", "replace").decode("latin-1")

class AgriSmartPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(46, 125, 50)  # Green color
        self.cell(0, 10, "AgriSmart - Laporan Rekomendasi", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, safe_text(f"Halaman {self.page_no()} | Dicetak pada {datetime.now().strftime('%d/%m/%Y %H:%M')}"), 0, 0, "C")

def generate_pupuk_pdf(data):
    pdf = AgriSmartPDF()
    pdf.add_page()
    
    # Judul & Info Dasar
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, safe_text(f"Rekomendasi Pupuk: {data.get('jenis_tanaman', '-').upper()}"), 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, safe_text(f"Sesi ID: {data.get('sesi_id', '-')}"), 0, 1)
    pdf.cell(0, 7, safe_text(f"Fase Tumbuh: {data.get('fase_tumbuh', '-')}"), 0, 1)
    pdf.cell(0, 7, safe_text(f"Luas Lahan: {data.get('luas_lahan', '-')} Hektar"), 0, 1)
    pdf.ln(5)

    # Kondisi Tanah
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " 1. Kondisi Tanah & Lingkungan", 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 10)
    kondisi = data.get("kondisi_tanah", {})
    pdf.cell(45, 7, safe_text(f"pH Tanah: {kondisi.get('ph_tanah', '-')}"), 0, 0)
    pdf.cell(45, 7, safe_text(f"Status pH: {kondisi.get('status_ph', '-')}"), 0, 1)
    pdf.cell(45, 7, safe_text(f"Nitrogen (N): {kondisi.get('nitrogen', '-')}"), 0, 0)
    pdf.cell(45, 7, safe_text(f"Status N: {kondisi.get('status_n', '-')}"), 0, 1)
    pdf.cell(45, 7, safe_text(f"Fosfor (P): {kondisi.get('fosfor', '-')}"), 0, 0)
    pdf.cell(45, 7, safe_text(f"Status P: {kondisi.get('status_p', '-')}"), 0, 1)
    pdf.cell(45, 7, safe_text(f"Kalium (K): {kondisi.get('kalium', '-')}"), 0, 0)
    pdf.cell(45, 7, safe_text(f"Status K: {kondisi.get('status_k', '-')}"), 0, 1)
    pdf.ln(5)

    # Ringkasan & Kesesuaian
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, " 2. Ringkasan Analisis", 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 7, safe_text(f"Kondisi: {data.get('kondisi_ringkasan', '-')}"))
    pdf.cell(0, 7, safe_text(f"Skor Kesesuaian: {data.get('kesesuaian_tanaman', {}).get('skor', '-')}/100"), border=0, ln=1)
    pdf.multi_cell(190, 7, safe_text(f"Saran: {data.get('kesesuaian_tanaman', {}).get('saran', '-')}"))
    pdf.ln(5)

    # Daftar Pupuk
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, " 3. Rekomendasi Pemupukan", 0, 1, "L", True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 8, "Nama Pupuk", 1, 0, "C")
    pdf.cell(40, 8, "Dosis", 1, 0, "C")
    pdf.cell(90, 8, "Cara Aplikasi", 1, 1, "C")
    
    pdf.set_font("Helvetica", "", 9)
    for p in data.get("daftar_pupuk", []):
        nama = str(p.get("nama_pupuk", p.get("nama", "-")))
        dosis = str(p.get("takaran_total", p.get("dosis", "-")))
        cara = str(p.get("metode_aplikasi", p.get("cara_aplikasi", "-")))
        
        pdf.cell(60, 8, safe_text(nama), 1, 0)
        pdf.cell(40, 8, safe_text(dosis), 1, 0)
        pdf.multi_cell(90, 8, safe_text(cara), border=1, ln=1)
    pdf.ln(5)

    # Jadwal
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, " 4. Jadwal Aplikasi & Catatan", 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 7, safe_text(f"Jadwal: {data.get('jadwal_aplikasi', '-')}"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Catatan Penting:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 7, safe_text(data.get("catatan_penting", "-")))
    
    return pdf.output()

def generate_pestisida_pdf(data):
    pdf = AgriSmartPDF()
    pdf.add_page()
    
    # Judul & Info Dasar
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, safe_text(f"Rekomendasi Pengendalian Hama: {data.get('jenis_hama', '-').upper()}"), 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, safe_text(f"Tanaman: {data.get('jenis_tanaman', '-')}"), 0, 1)
    pdf.cell(0, 7, safe_text(f"Tingkat Serangan: {data.get('tingkat_serangan', '-')}"), 0, 1)
    pdf.cell(0, 7, safe_text(f"Luas Lahan: {data.get('luas_lahan', '-')} Hektar"), 0, 1)
    pdf.ln(5)

    # Identifikasi
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " 1. Identifikasi Hama/Penyakit", 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 10)
    ident = data.get("identifikasi", {})
    pdf.cell(0, 7, safe_text(f"Nama: {ident.get('nama_latin', ident.get('nama_umum', '-'))}"), border=0, ln=1)
    pdf.multi_cell(190, 7, safe_text(f"Gejala: {ident.get('gejala', '-')}"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Strategi Pengendalian:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 7, safe_text(data.get("strategi_pengendalian", "-")))
    pdf.ln(5)

    # Daftar Pestisida
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, " 2. Rekomendasi Pestisida", 0, 1, "L", True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 8, "Nama/Bahan Aktif", 1, 0, "C")
    pdf.cell(40, 8, "Dosis/Konsentrasi", 1, 0, "C")
    pdf.cell(60, 8, "Waktu Semprot", 1, 0, "C")
    pdf.cell(40, 8, "PHI", 1, 1, "C")
    
    pdf.set_font("Helvetica", "", 9)
    for p in data.get("daftar_pestisida", []):
        nama = str(p.get("nama_pestisida", p.get("nama", "-")))
        dosis = str(p.get("dosis_per_liter_air", p.get("dosis", "-")))
        waktu = str(p.get("waktu_aplikasi", p.get("waktu_semprot", "-")))
        phi = str(p.get("phi", "-"))
        
        pdf.cell(50, 8, safe_text(nama), 1, 0)
        pdf.cell(40, 8, safe_text(dosis), 1, 0)
        pdf.cell(60, 8, safe_text(waktu), 1, 0)
        pdf.cell(40, 8, safe_text(phi), 1, 1)
    pdf.ln(5)

    # Keamanan & Peringatan
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, " 3. Catatan Keamanan & Peringatan", 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 7, safe_text(f"Keamanan: {data.get('catatan_keamanan', '-')}"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 7, "Peringatan:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    for warn in data.get("peringatan", []):
        pdf.multi_cell(190, 7, safe_text(f"- {warn}"))
    pdf.set_text_color(0, 0, 0)
    
    return pdf.output()
    
    return pdf.output()
