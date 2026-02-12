"""
Django settings for HRMS project.
"""

from pathlib import Path
import os
import sys
import mongoengine
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# BASE DIRECTORY
# -------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
# -------------------------------------------------------------------------
load_dotenv(os.path.join(BASE_DIR, ".env"))

# -------------------------------------------------------------------------
# SECURITY SETTINGS
# -------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-key")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "http://localhost:5173",
    "*",
    "distillatory-neoma-unmoldy.ngrok-free.dev",
    "localhost",
    "127.0.0.1",
    "192.168.1.35",
    ".vercel.app",
    "https://*.vercel.app",
    
]

# -------------------------------------------------------------------------
# INSTALLED APPS
# -------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_mongoengine',
    "corsheaders",

    # Local apps
    'Orgnization',
    'Employee',
    'Departments',
    'Shifts',
    "Leave",
]

# -------------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be at top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------------------------------------------------
# CORS & CSRF
# -------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
    'x-user-id',
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "https://distillatory-neoma-unmoldy.ngrok-free.dev",
]

# -------------------------------------------------------------------------
# URL CONFIG
# -------------------------------------------------------------------------
ROOT_URLCONF = 'HRMS.urls'

# -------------------------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'HRMS.wsgi.application'

# -------------------------------------------------------------------------
# DISABLE DJANGO ORM (using MongoEngine)
# -------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}

# -------------------------------------------------------------------------
# MONGOENGINE CONFIG WITH TIMEZONE AWARENESS
# -------------------------------------------------------------------------
MONGO_DB = os.getenv("MONGO_DB")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")

if not all([MONGO_DB, MONGO_USER, MONGO_PASS, MONGO_CLUSTER]):
    print("❌ Missing MongoDB environment variables.")
    sys.exit(1)

mongoengine.connect(
    db=MONGO_DB,
    host=f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority",
    alias="default",
    tz_aware=True,  # CRITICAL: Ensures timezone-aware datetime objects
    tzinfo=None     # Let Python handle timezone conversion
)

# -------------------------------------------------------------------------
# PASSWORD VALIDATORS
# -------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------------------------------
# INTERNATIONALIZATION & TIMEZONE SETTINGS
# -------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'

# CRITICAL TIMEZONE SETTINGS
TIME_ZONE = 'Asia/Kolkata'  # Default timezone for the application
USE_I18N = True
USE_TZ = True  # MUST be True for timezone-aware datetime objects

# -------------------------------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "assets")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEBUG = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB

# File upload handlers
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FILE_UPLOAD_PERMISSIONS = 0o644

# -------------------------------------------------------------------------
# DRF SETTINGS (IMPORTANT FOR JWT)
# -------------------------------------------------------------------------
REST_FRAMEWORK = {
    
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'HRMS.auth.MongoJWTAuthentication',  # your custom JWT auth
    ],
    
    # Add timezone settings for DRF
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATETIME_INPUT_FORMATS': ['%Y-%m-%d %H:%M:%S', 'iso-8601'],
}

# -------------------------------------------------------------------------
# EMAIL SETTINGS
# -------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'vishaltarale055@gmail.com'
EMAIL_HOST_PASSWORD = "lyrllnhycsywomtq"



# settings.py

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_ENABLE_UTC = False
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Optional: Task result expiration (7 days)
CELERY_RESULT_EXPIRES = 60 * 60 * 24 * 7

# Optional: Task time limit (10 minutes)
CELERY_TASK_TIME_LIMIT = 10 * 60