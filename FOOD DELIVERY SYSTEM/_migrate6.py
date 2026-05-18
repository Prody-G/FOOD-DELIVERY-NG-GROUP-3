"""Migration 6:
- Add riders.profile_picture
- Create item_addon_groups table
- Create item_addons table
- Create order_item_addons table
"""
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

def create_table(sql):
    try:
        cur.execute(sql)
        print(f"  Created table")
    except sqlite3.OperationalError as e:
        if 'already exists' in str(e).lower():
            print(f"  (skip) table already exists")
        else:
            raise

# ── riders.profile_picture ────────────────────────────────────────────────────
add_column('riders', 'profile_picture', 'TEXT')

# ── item_addon_groups ─────────────────────────────────────────────────────────
create_table("""
CREATE TABLE item_addon_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES menu_items(id),
    name TEXT NOT NULL,
    required INTEGER DEFAULT 0,
    max_selections INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)""")

# ── item_addons ───────────────────────────────────────────────────────────────
create_table("""
CREATE TABLE item_addons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES item_addon_groups(id),
    name TEXT NOT NULL,
    price REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)""")

# ── order_item_addons ─────────────────────────────────────────────────────────
create_table("""
CREATE TABLE order_item_addons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id),
    addon_id INTEGER REFERENCES item_addons(id),
    name TEXT NOT NULL,
    price REAL DEFAULT 0.0
)""")

conn.commit()
conn.close()
print("Migration 6 complete.")
