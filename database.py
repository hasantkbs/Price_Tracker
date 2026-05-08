import os
import sqlite3
import datetime

DB_PATH = os.getenv("DB_PATH", "price_tracker.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id             TEXT NOT NULL,
        url                 TEXT NOT NULL,
        name                TEXT,
        target_price        REAL NOT NULL,
        current_price       REAL,
        initial_price       REAL,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked_at     TIMESTAMP,
        price_selector      TEXT,
        alert_price         REAL,
        alert_enabled       INTEGER DEFAULT 0,
        selector_fail_count INTEGER DEFAULT 0,
        last_error          TEXT,
        last_price_source   TEXT,
        UNIQUE(user_id, url)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id  INTEGER NOT NULL,
        price       REAL NOT NULL,
        source      TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_product ON price_history(product_id, recorded_at DESC);"
    )
    
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_user ON products(user_id);"
    )

    conn.commit()
    conn.close()
    _migrate_schema()
    print("Veritabanı başarıyla kuruldu/güncellendi.")


def _migrate_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    # Check for user_id column
    if "user_id" not in columns:
        # This is a major migration because of the UNIQUE constraint change.
        # For simplicity in this environment, we'll just add the column if missing.
        # In a real app, you'd need a more complex migration to handle existing data.
        cursor.execute("ALTER TABLE products ADD COLUMN user_id TEXT DEFAULT 'default_user'")
        print("Şema güncellendi: 'user_id' eklendi.")
        
    migrations = [
        ("price_selector",      "ALTER TABLE products ADD COLUMN price_selector TEXT"),
        ("name",                "ALTER TABLE products ADD COLUMN name TEXT"),
        ("alert_price",         "ALTER TABLE products ADD COLUMN alert_price REAL"),
        ("alert_enabled",       "ALTER TABLE products ADD COLUMN alert_enabled INTEGER DEFAULT 0"),
        ("selector_fail_count", "ALTER TABLE products ADD COLUMN selector_fail_count INTEGER DEFAULT 0"),
        ("last_error",          "ALTER TABLE products ADD COLUMN last_error TEXT"),
        ("last_price_source",   "ALTER TABLE products ADD COLUMN last_price_source TEXT"),
    ]
    for col_name, sql in migrations:
        if col_name not in columns:
            cursor.execute(sql)
            print(f"Şema güncellendi: '{col_name}' eklendi.")
    conn.commit()
    conn.close()


# ── Products ──────────────────────────────────────────────────────────────────

def add_product(user_id, url, target_price, initial_price, selector, name=None):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO products "
            "(user_id, url, name, target_price, initial_price, current_price, price_selector) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, url, name, target_price, initial_price, initial_price, selector),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Bu ürün ({url}) zaten takip ediliyor.")
    finally:
        conn.close()


def get_all_products(user_id=None):
    conn = get_db_connection()
    if user_id:
        rows = conn.execute("SELECT * FROM products WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id: int, user_id: str = None):
    conn = get_db_connection()
    if user_id:
        row = conn.execute("SELECT * FROM products WHERE id = ? AND user_id = ?", (product_id, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return row


def get_product_by_url(user_id, url: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM products WHERE user_id = ? AND url = ?", (user_id, url)).fetchone()
    conn.close()
    return row


def update_product_price(product_id, new_price, source: str = "unknown"):
    now = datetime.datetime.now().isoformat()
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET current_price=?, last_checked_at=?, "
        "last_price_source=?, selector_fail_count=0, last_error=NULL WHERE id=?",
        (new_price, now, source, product_id),
    )
    conn.commit()
    conn.close()


def update_product_fields(product_id, user_id, name=None, target_price=None,
                          alert_price=None, alert_enabled=None):
    conn = get_db_connection()
    fields, values = [], []
    if name is not None:
        fields.append("name = ?");          values.append(name)
    if target_price is not None:
        fields.append("target_price = ?");  values.append(target_price)
    if alert_price is not None:
        fields.append("alert_price = ?");   values.append(alert_price)
    if alert_enabled is not None:
        fields.append("alert_enabled = ?"); values.append(1 if alert_enabled else 0)
    if fields:
        values.append(product_id)
        values.append(user_id)
        conn.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ? AND user_id = ?", values)
        conn.commit()
    conn.close()


def update_product_alert(product_id, user_id, alert_price, alert_enabled):
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET alert_price=?, alert_enabled=? WHERE id=? AND user_id = ?",
        (alert_price, 1 if alert_enabled else 0, product_id, user_id),
    )
    conn.commit()
    conn.close()


def update_product_selector(product_id, new_selector: str):
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET price_selector=?, selector_fail_count=0, last_error=NULL WHERE id=?",
        (new_selector, product_id),
    )
    conn.commit()
    conn.close()


def record_selector_failure(product_id, error_msg: str = ""):
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET selector_fail_count = selector_fail_count + 1, last_error=? WHERE id=?",
        (error_msg, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id: int, user_id: str):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    conn.commit()
    conn.close()



# ── Price History ─────────────────────────────────────────────────────────────

def add_price_history(product_id: int, price: float, source: str = "unknown"):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO price_history (product_id, price, source) VALUES (?, ?, ?)",
        (product_id, price, source),
    )
    conn.commit()
    conn.close()


def get_price_history(product_id: int, limit: int = 60):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT price, source, recorded_at FROM price_history "
        "WHERE product_id = ? ORDER BY recorded_at DESC LIMIT ?",
        (product_id, limit),
    ).fetchall()
    conn.close()
    return rows


if __name__ == '__main__':
    setup_database()
