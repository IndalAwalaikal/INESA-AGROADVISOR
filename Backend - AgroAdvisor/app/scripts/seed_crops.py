import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "agrismart")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

CROPS = [
    ("Padi Sawah", 120, 60, 50, 5.0, 7.0, "High"),
    ("Jagung", 180, 90, 75, 5.8, 7.2, "Medium"),
    ("Kedelai", 50, 60, 60, 6.0, 7.0, "Medium"),
    ("Kacang Tanah", 40, 60, 50, 5.5, 6.5, "Medium"),
    ("Singkong", 120, 60, 150, 5.2, 7.0, "Low"),
    ("Ubi Jalar", 80, 60, 120, 5.5, 6.5, "Medium"),
    ("Cabai Merah", 150, 100, 120, 6.0, 7.0, "Medium"),
    ("Tomat", 140, 90, 160, 6.0, 6.8, "Medium"),
    ("Bawang Merah", 120, 90, 100, 6.0, 7.0, "Medium"),
    ("Kentang", 150, 120, 200, 5.0, 6.5, "Medium"),
    ("Kubis (Kol)", 160, 100, 140, 6.0, 7.0, "High"),
    ("Terong", 130, 80, 120, 5.5, 6.8, "Medium"),
    ("Mentimun", 100, 80, 120, 5.5, 6.8, "High"),
    ("Kacang Panjang", 60, 80, 80, 5.5, 6.5, "Medium"),
    ("Sawi / Pakcoy", 100, 60, 80, 6.0, 7.0, "High"),
    ("Bayam", 80, 50, 60, 6.0, 7.0, "High"),
    ("Kangkung", 90, 50, 70, 5.5, 7.0, "High"),
    ("Wortel", 100, 80, 150, 5.5, 6.5, "Medium"),
    ("Semangka", 120, 90, 140, 5.8, 7.2, "Medium"),
    ("Melon", 140, 100, 160, 6.0, 7.0, "Medium"),
    ("Kelapa Sawit (TM)", 160, 90, 220, 4.0, 6.0, "High"),
    ("Karet", 100, 60, 100, 4.5, 6.5, "High"),
    ("Kopi", 140, 80, 150, 5.5, 6.5, "Medium"),
    ("Kakao", 120, 90, 160, 6.0, 7.0, "Medium"),
    ("Tebu", 180, 100, 160, 5.5, 7.5, "High"),
    ("Teh", 200, 60, 100, 4.5, 5.5, "High"),
    ("Tembakau", 80, 100, 150, 5.5, 6.5, "Medium"),
    ("Kelapa", 120, 80, 180, 5.5, 7.5, "Medium"),
    ("Lada", 120, 90, 140, 5.5, 6.5, "High"),
    ("Cengkeh", 100, 60, 120, 5.0, 6.5, "Medium"),
    ("Jeruk", 150, 80, 140, 5.5, 6.5, "Medium"),
    ("Mangga", 120, 80, 150, 5.5, 7.0, "Low"),
    ("Pisang", 200, 80, 300, 5.5, 7.5, "High"),
    ("Nanas", 150, 60, 180, 4.5, 5.5, "Low"),
    ("Pepaya", 140, 90, 180, 6.0, 7.0, "Medium"),
    ("Durian", 130, 90, 160, 5.5, 6.5, "Medium"),
    ("Alpukat", 110, 70, 140, 5.5, 6.5, "Medium"),
    ("Manggis", 90, 60, 110, 5.0, 6.5, "Medium"),
    ("Jahe", 120, 80, 150, 5.5, 7.0, "Medium"),
    ("Nilam", 140, 70, 120, 5.5, 7.0, "Medium"),
    ("Bawang Putih", 120, 100, 120, 6.0, 7.5, "Medium"),
    ("Buncis", 70, 90, 90, 5.5, 6.5, "Medium"),
    ("Brokoli", 160, 90, 140, 6.0, 7.0, "High"),
    ("Seledri", 140, 80, 120, 6.0, 7.0, "High"),
    ("Selada", 90, 60, 90, 6.0, 7.0, "High"),
    ("Labu Siam", 100, 80, 120, 5.5, 6.5, "High"),
    ("Pare", 110, 80, 130, 5.5, 6.8, "Medium"),
    ("Labu Kuning", 120, 90, 140, 5.5, 7.0, "Medium"),
    ("Jambu Biji", 100, 60, 120, 5.0, 6.5, "Medium"),
    ("Rambutan", 120, 70, 130, 5.5, 6.5, "Medium"),
    ("Kelengkeng", 130, 80, 150, 5.5, 6.5, "Medium"),
    ("Salak", 100, 60, 140, 5.0, 6.5, "High"),
    ("Sirsak", 90, 60, 110, 5.5, 6.5, "Medium"),
    ("Vanili", 80, 60, 100, 5.5, 7.0, "High"),
    ("Kayu Manis", 100, 50, 80, 4.5, 6.0, "Medium"),
    ("Kapulaga", 120, 80, 140, 5.0, 6.5, "High"),
    ("Kunyit", 100, 80, 140, 5.5, 7.0, "Medium"),
    ("Temulawak", 100, 80, 130, 5.0, 6.5, "Medium"),
    ("Krisan (Bunga)", 150, 100, 150, 5.5, 6.5, "High"),
    ("Mawar (Potong)", 160, 120, 160, 6.0, 7.0, "High"),
]

def seed():
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
            cursor.execute("DELETE FROM kebutuhan_hara")
            
            sql = """
                INSERT INTO kebutuhan_hara (nama_tanaman, n_req, p_req, k_req, ph_min, ph_max, kebutuhan_air)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, CROPS)
            conn.commit()
            print(f"Successfully seeded {len(CROPS)} crops into kebutuhan_hara table.")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
