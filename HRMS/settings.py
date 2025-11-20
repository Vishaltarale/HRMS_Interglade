"""
Django settings for HRMS project.
"""

from pathlib import Path
import os
import sys
import mongoengine
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Base directory setup
# -------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------------
load_dotenv(os.path.join(BASE_DIR, ".env"))

# -------------------------------------------------------------------------
# SECURITY SETTINGS
# -------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-key")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "*",
    "distillatory-neoma-unmoldy.ngrok-free.dev",
    "localhost",
    "127.0.0.1",
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

    # Third-party apps
    'rest_framework',
    'rest_framework_mongoengine',
    "corsheaders",

    # Local apps
    'Orgnization',
    'Employee',
    'Departments',
    'Shifts',
]

# -------------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # MUST be at top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------------------------------------------------
# CORS & CSRF CONFIG
# -------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True  # allow React frontend

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "ngrok-skip-browser-warning",
]

CSRF_TRUSTED_ORIGINS = [
    "https://distillatory-neoma-unmoldy.ngrok-free.dev",
]

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
# DISABLE DJANGO ORM (we use MongoEngine)
# -------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}

# -------------------------------------------------------------------------
# MONGOENGINE CONNECTION
# -------------------------------------------------------------------------
MONGO_DB = os.getenv("MONGO_DB")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")

if not all([MONGO_DB, MONGO_USER, MONGO_PASS, MONGO_CLUSTER]):
    print("❌ Missing MongoDB environment variables.")
    print(f"MONGO_USER={MONGO_USER}, MONGO_PASS={MONGO_PASS}, MONGO_CLUSTER={MONGO_CLUSTER}")
    sys.exit(1)

mongoengine.connect(
    db=MONGO_DB,
    host=f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority",
    alias='default',
    tz_aware=True
)

# -------------------------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------------
# STATIC & MEDIA
# -------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "assets")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



#Rest_Framework Related all info here .......
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  
}
