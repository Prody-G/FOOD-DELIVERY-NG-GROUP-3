from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    cols = [
        ('riders', 'is_online', 'BOOLEAN DEFAULT 0'),
        ('riders', 'location', 'VARCHAR(255)'),
        ('vendors', 'business_address', 'VARCHAR(255)'),
        ('vendors', 'proposal', 'TEXT'),
    ]
    for table, col, typ in cols:
        try:
            db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {typ}'))
            db.session.commit()
            print(f'Added {table}.{col}')
        except Exception as e:
            db.session.rollback()
            print(f'Skip {table}.{col}: {e}')
    print('Done')
