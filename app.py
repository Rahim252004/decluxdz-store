import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///decluxdz.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
# Create upload directory if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config['WTF_CSRF_ENABLED'] = False

# Initialize the app with the extension
db.init_app(app)

# بعد db.init_app(app) في ملف الإعداد (مثال: app.py)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# تفعيل CSRF على التطبيق
csrf = CSRFProtect()
csrf.init_app(app)

# جعل دالة csrf_token متاحة في القوالب (تتيح لك استخدام {{ csrf_token() }})
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# ---- خيارات أمان مقترحة ----
# تأكد من وجود SECRET_KEY قوي في بيئة الإنتاج (نستخدم env var بالفعل في كودك)
# يُنصح أيضاً ضبط cookies بالأمان التالي (اختياري):
app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')  # أو 'Strict' حسب حاجتك
# --------------------------------




with app.app_context():
    # Import models so their tables are created
    import models
    
    # Import routes
    import routes
    import admin_routes
    import api_routes
    
    db.create_all()
    
    # Create default admin user if none exists
    from models import Admin
    from werkzeug.security import generate_password_hash
    
    if not Admin.query.first():
        admin = Admin(
            username="Zaki",
            email="luxurydeco213@gmail.com",
            password_hash=generate_password_hash("@Zaki25")
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created: Zaki/@Zaki25")
        
