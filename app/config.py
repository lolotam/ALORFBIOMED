import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = secrets.token_hex(32)
    DEBUG = True  # Enable debug for development

    # Database configuration - use local SQLite database for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///equipment_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = 'data'

    # Enable scheduler for development
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'

    # Use absolute paths for data files in development
    PPM_JSON_PATH = os.path.join('data', 'ppm.json')
    OCM_JSON_PATH = os.path.join('data', 'ocm.json')
    TRAINING_JSON_PATH = os.path.join('data', 'training.json')
    SETTINGS_JSON_PATH = os.path.join('data', 'settings.json')
    AUDIT_LOG_JSON_PATH = os.path.join('data', 'audit_log.json')
    PUSH_SUBSCRIPTIONS_JSON_PATH = os.path.join('data', 'push_subscriptions.json')

    # Session Configuration for development
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = False  # Allow non-HTTPS in development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Reminder system configuration
    REMINDER_DAYS = 60  # Default days ahead to check for maintenance

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-16-digit-app-password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Push notification configuration  
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:dr.vet.waledmohamed@gmail.com')

    # Mailjet Email API configuration (primary email service)
    MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
    MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY')
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'dr.vet.waledmohamed@gmail.com')
    EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER', 'alorfbiomed@gmail.com')



