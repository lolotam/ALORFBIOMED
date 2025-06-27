import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key'  # Use env var in production
    DEBUG = os.environ.get('FLASK_ENV') != 'production'  # Disable debug in production

    # Database configuration - use relative paths or memory for Vercel
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = 'data'

    # Disable scheduler for serverless deployment (can be overridden by env var)
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'false').lower() == 'true'

    # Use relative paths for data files
    PPM_JSON_PATH = os.path.join('app', 'data', 'ppm.json')
    OCM_JSON_PATH = os.path.join('app', 'data', 'ocm.json')
    TRAINING_JSON_PATH = os.path.join('app', 'data', 'training.json')
    SETTINGS_JSON_PATH = os.path.join('app', 'data', 'settings.json')
    AUDIT_LOG_JSON_PATH = os.path.join('app', 'data', 'audit_log.json')
    PUSH_SUBSCRIPTIONS_JSON_PATH = os.path.join('app', 'data', 'push_subscriptions.json')

    # Session Configuration - use secure cookies for serverless
    SESSION_TYPE = 'null'  # Use null session for serverless (stateless)
    SESSION_PERMANENT = False  # Don't use permanent sessions in serverless
    SESSION_USE_SIGNER = True  # Sign the session cookie for extra security
    SESSION_COOKIE_SECURE = True  # Use secure cookies in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection



