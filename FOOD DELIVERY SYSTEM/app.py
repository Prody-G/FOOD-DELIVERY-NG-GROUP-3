from flask import Flask
from config import Config
from models import db, Admin
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'banners'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'items'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'delivery_proofs'), exist_ok=True)

    db.init_app(app)

    from routes.admin import admin_bp
    from routes.rider import rider_bp
    from routes.vendor import vendor_bp
    from routes.customer import customer_bp

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(rider_bp, url_prefix='/rider')
    app.register_blueprint(vendor_bp, url_prefix='/vendor')
    app.register_blueprint(customer_bp)

    with app.app_context():
        db.metadata.create_all(db.engine, checkfirst=True)
        # Seed default admin account
        if not Admin.query.first():
            admin = Admin(username='admin', email='admin@fooddelivery.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@fooddelivery.com / admin123")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
