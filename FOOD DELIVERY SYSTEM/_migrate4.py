"""Migration 4: Add shipping_fee, distance_km to orders; vendor_barangay, shop_type to vendors."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_delivery.db')
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def add_column(table, col, col_type, default=None):
    try:
        if default is not None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}")
        else:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        print(f"  Added {table}.{col}")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f"  (skip) {table}.{col} already exists")
        else:
            raise

add_column('orders',  'shipping_fee', 'REAL', 0.0)
add_column('orders',  'distance_km',  'REAL')
add_column('vendors', 'vendor_barangay', 'TEXT')
add_column('vendors', 'shop_type', "TEXT DEFAULT 'restaurant'")

conn.commit()
conn.close()
print("Migration 4 complete.")
