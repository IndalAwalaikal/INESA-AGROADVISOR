import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "agrismart")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Data: (tanaman, kategori, nama_umum, nama_ilmiah, gejala, produk)
PESTS = [
    ("Padi Sawah", "hama", "Wereng Coklat", "Nilaparvata lugens", "Daun menguning dan kering melingkar (hopperburn)", "Regent 50SC, Virtako 300SC"),
    ("Padi Sawah", "hama", "Penggerek Batang", "Scirpophaga incertulas", "Pucuk layu (sundep) atau malai hampa (beluk)", "Prevathon, Furadan 3G"),
    ("Padi Sawah", "penyakit", "Blas", "Pyricularia oryzae", "Bercak belah ketupat pada daun, busuk leher malai", "Antracol, Amistartop"),
    ("Padi Sawah", "gulma", "Eceng Padi", "Monochoria vaginalis", "Persaingan hara di sawah genangan", "Nominee 100SC"),
    
    ("Jagung", "hama", "Ulat Grayak (FAW)", "Spodoptera frugiperda", "Daun berlubang besar, terdapat kotoran seperti serbuk gergaji", "Prevathon, Buldok 25EC"),
    ("Jagung", "penyakit", "Bule", "Peronosclerospora maydis", "Daun berwarna putih/kuning bergaris, tanaman kerdil", "Ridomil Gold, sarana benih"),
    
    ("Cabai Merah", "hama", "Thrips", "Thrips parvispinus", "Daun mengeriting ke atas, bercak perak di bawah daun", "Curacron, Demolish 18EC"),
    ("Cabai Merah", "penyakit", "Antraknosa (Patek)", "Colletotrichum capsici", "Bercak coklat kehitaman melingkar pada buah", "Antracol, Score 250EC"),
    
    ("Bawang Merah", "hama", "Ulat Grayak", "Spodoptera exigua", "Ulat masuk ke dalam daun bawang, daun terlihat transparan", "Prevathon, Brofreya"),
    ("Bawang Merah", "penyakit", "Moler (Layu Fusarium)", "Fusarium oxysporum", "Daun terpelintir/melengkung, akar membusuk", "Topsin M, Nordox 56WP"),
    
    ("Tomat", "hama", "Kutu Kebul", "Bemisia tabaci", "Daun menguning, lengket (embun jelaga), vektor virus", "Pegasus 500SC, Movento"),
    ("Tomat", "penyakit", "Busuk Daun", "Phytophthora infestans", "Bercak basah kehitaman pada daun dan buah", "Daconil, Recado"),
]

def seed_pests():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            # Clear existing data
            cursor.execute("DELETE FROM master_hama_penyakit")
            
            sql = """
                INSERT INTO master_hama_penyakit 
                (nama_tanaman, kategori, nama_umum, nama_ilmiah, gejala_utama, saran_produk)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, PESTS)
            conn.commit()
            print(f"Successfully seeded {len(PESTS)} pest records into master_hama_penyakit table.")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_pests()
