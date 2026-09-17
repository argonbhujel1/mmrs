import os
from dotenv import load_dotenv

load_dotenv()

def _is_vercel():
    return bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

def _upload_folder():
    # Vercel / serverless: only /tmp is writable
    if _is_vercel() or os.environ.get('UPLOAD_FOLDER'):
        return os.environ.get('UPLOAD_FOLDER') or '/tmp/morang_uploads'
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')

def _database_uri():
    uri = os.environ.get('DATABASE_URL') or ''
    if not uri:
        if _is_vercel():
            # Ephemeral but allows app to boot without Postgres; prefer real DATABASE_URL
            return 'sqlite:////tmp/morang_model.db'
        return 'sqlite:///morang_model.db'
    # Heroku/Vercel sometimes give postgres:// — SQLAlchemy needs postgresql://
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    return uri

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-morang-model-2026'
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = _upload_folder()
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'txt', 'csv', 'zip', 'rar', '7z',
        'mp3', 'mp4', 'avi', 'mov'
    }
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME', 'noreply@morangmodel.com')
    
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
