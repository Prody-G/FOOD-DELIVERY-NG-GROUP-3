import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'food_delivery.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

existing = [r[1] for r in cur.execute("PRAGMA table_info(vendors)").fetchall()]
added = []

for col, ddl in [
    ('shop_logo',      'VARCHAR(255)'),
    ('business_city',  'VARCHAR(100)'),
]:
    if col not in existing:
        cur.execute(f'ALTER TABLE vendors ADD COLUMN {col} {ddl}')
        added.append(col)

conn.commit()
conn.close()
print('Added:', added if added else 'nothing new')
