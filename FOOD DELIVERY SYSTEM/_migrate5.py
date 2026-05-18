"""Migration 5: Add start_time, end_time, is_open_shift to rider_shifts."""
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

add_column('rider_shifts', 'start_time',    'TEXT')
add_column('rider_shifts', 'end_time',      'TEXT')
add_column('rider_shifts', 'is_open_shift', 'INTEGER', 0)

conn.commit()
conn.close()
print("Migration 5 complete.")
