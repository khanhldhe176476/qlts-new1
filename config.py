import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (does not override existing env)
load_dotenv()

class Config:
    # Provide sensible local defaults so the app can boot for development
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///./instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('1', 'true', 'yes')  # Default to True for development
    EXPORT_DIR = os.getenv('EXPORT_DIR', 'instance/exports')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'instance/uploads')
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 10485760))  # 10MB default
    ALLOWED_EXTENSIONS = {
        'pdf',
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tif', 'tiff', 'ico', 'avif',
        'doc', 'docx', 'xls', 'xlsx'
    }
    # Optional bootstrap config for first-run initialization
    INIT_TOKEN = os.getenv('INIT_TOKEN', '')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'mh123#@!')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@mhsolution.vn')
    
    # Email configuration (disabled by default)
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    MAIL_SERVER = os.getenv('MAIL_SERVER', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Application URL for general links
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)  # Sử dụng SECRET_KEY nếu không có JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token hết hạn sau 24 giờ
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Refresh token hết hạn sau 30 ngày