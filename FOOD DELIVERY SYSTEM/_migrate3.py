"""Migration 3 — Add delivery_phase to orders, metrics to riders,
   create rider_shifts, rider_ratings, chat_messages tables."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_delivery.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ── Order.delivery_phase ──────────────────────────────────────────────────────
try:
    c.execute("ALTER TABLE orders ADD COLUMN delivery_phase VARCHAR(30) DEFAULT 'going_to_vendor'")
    print("Added orders.delivery_phase")
except Exception as e:
    print(f"orders.delivery_phase: {e}")

# ── Rider performance columns ─────────────────────────────────────────────────
for col, typ, default in [
    ('avg_rating',    'REAL',    '5.0'),
    ('total_ratings', 'INTEGER', '0'),
    ('total_accepted','INTEGER', '0'),
    ('total_offered', 'INTEGER', '0'),
]:
    try:
        c.execute(f"ALTER TABLE riders ADD COLUMN {col} {typ} DEFAULT {default}")
        print(f"Added riders.{col}")
    except Exception as e:
        print(f"riders.{col}: {e}")

# ── rider_shifts ──────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS rider_shifts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    rider_id   INTEGER NOT NULL REFERENCES riders(id),
    zone       VARCHAR(100),
    shift_date DATE    NOT NULL,
    time_slot  VARCHAR(50),
    status     VARCHAR(20) DEFAULT 'booked',
    created_at DATETIME   DEFAULT CURRENT_TIMESTAMP
)''')
print("rider_shifts table ready")

# ── rider_ratings ─────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS rider_ratings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rider_id    INTEGER NOT NULL REFERENCES riders(id),
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    rating      INTEGER NOT NULL,
    comment     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
print("rider_ratings table ready")

# ── chat_messages ─────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    sender_type VARCHAR(10) NOT NULL,
    sender_id   INTEGER NOT NULL,
    message     TEXT    NOT NULL,
    sent_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read     INTEGER  DEFAULT 0
)''')
print("chat_messages table ready")

conn.commit()
conn.close()
print("Migration 3 complete.")
