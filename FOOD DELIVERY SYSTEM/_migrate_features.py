import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_delivery.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE customers ADD COLUMN id_document TEXT")
    print("Added id_document to customers.")
except Exception as e:
    print(e)

try:
    cur.execute("ALTER TABLE riders ADD COLUMN current_lat REAL")
    cur.execute("ALTER TABLE riders ADD COLUMN current_lng REAL")
    print("Added current_lat/lng to riders.")
except Exception as e:
    print(e)

try:
    cur.execute("ALTER TABLE rider_cashouts ADD COLUMN vendor_id INTEGER REFERENCES vendors(id)")
    print("Added vendor_id to rider_cashouts.")
except Exception as e:
    print(e)

# Also update existing customers to 'active' if they don't have an ID, to prevent locking out seeded users
cur.execute("UPDATE customers SET status = 'active' WHERE status IS NULL OR status = 'pending'")

conn.commit()
conn.close()
print("Migration complete.")
