import sqlite3
import datetime

def get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect('price_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_selector_column_if_not_exists():
    """Mevcut tabloya 'price_selector' kolonunu ekler (eğer yoksa)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tablo bilgilerini al
        cursor.execute("PRAGMA table_info(products)")
        columns = [row['name'] for row in cursor.fetchall()]
        # Kolon yoksa ekle
        if 'price_selector' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN price_selector TEXT")
            conn.commit()
            print("Veritabanı şeması güncellendi: 'price_selector' kolonu eklendi.")
    except Exception as e:
        print(f"Veritabanı güncellenirken hata oluştu: {e}")
    finally:
        conn.close()

def setup_database():
    """Veritabanını ve tabloyu oluşturur, gerekirse günceller."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        target_price REAL NOT NULL,
        current_price REAL,
        initial_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked_at TIMESTAMP,
        price_selector TEXT
    );
    """)
    conn.commit()
    conn.close()
    
    # Veritabanı şemasını kontrol et ve gerekirse güncelle
    add_selector_column_if_not_exists()
    print("Veritabanı başarıyla kuruldu/güncellendi.")

def add_product(url, target_price, initial_price, selector):
    """Veritabanına yeni bir ürün ekler (seçici ile birlikte)."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO products (url, target_price, initial_price, current_price, price_selector) VALUES (?, ?, ?, ?, ?)",
            (url, target_price, initial_price, initial_price, selector)
        )
        conn.commit()
        print(f"Ürün eklendi: {url}")
        print(f"   -> Kullanılacak Seçici: {selector}")
    except sqlite3.IntegrityError:
        print(f"Hata: Bu ürün ({url}) zaten takip ediliyor.")
    finally:
        conn.close()

def get_all_products():
    """Takip edilen tüm ürünleri getirir."""
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return products

def update_product_price(product_id, new_price):
    """Bir ürünün mevcut fiyatını ve son kontrol zamanını günceller."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET current_price = ?, last_checked_at = ? WHERE id = ?",
        (new_price, datetime.datetime.now(), product_id)
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()

