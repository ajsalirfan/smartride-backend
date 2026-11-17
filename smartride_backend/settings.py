import pymysql
pymysql.install_as_MySQLdb()
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import os
from datetime import timedelta
from decouple import config

# ==================== CORE SETTINGS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-smartride-ajsal-2024-backend')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [
    'localhost', '127.0.0.1', '0.0.0.0', '192.168.1.*',
    'testserver', '.smartride.com', '.vercel.app', '.railway.app',
]

AUTH_USER_MODEL = 'Users.CustomUser'

# ==================== INSTALLED APPS ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third Party
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'django_filters',
    'phonenumber_field',
    
    # Local Apps
    'Users.apps.UsersConfig',
    'Admin.apps.AdminConfig',
    'StaffWork.apps.StaffWorkConfig',
]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartride_backend.urls'
WSGI_APPLICATION = 'smartride_backend.wsgi.application'


# ==================== DATABASE ====================
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}


# ==================== PASSWORD VALIDATION ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ==================== STATIC & MEDIA ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== REST FRAMEWORK CONFIG ====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ==================== JWT CONFIG ====================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
# ==================== CORS & SESSION CONFIG ====================
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://smartride-frontend-seven.vercel.app",  # ✅ Vercel ലിങ്ക് ചേർത്തു
]
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# ... (Session Engine കോഡുകൾ അതേപടി ഇരിക്കട്ടെ) ...

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://smartride-frontend-seven.vercel.app",  # ✅ ഇവിടെയും ചേർക്കുക
]
# ==================== EMAIL CONFIG ====================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tommyshelbyy06@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('SMART_RIDE_EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = 'ajsalirfan56@gmail.com'
STAFF_EMAILS = ['ajsalirfan56@gmail.com']

# ==================== AUTH BACKENDS ====================
AUTHENTICATION_BACKENDS = [
    'Users.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ==================== SECURITY SETTINGS ====================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==================== TEMPLATE CONFIG ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # ✅ Global templates folder
        'APP_DIRS': True,                  # ✅ Enables templates inside apps
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==================== SMART RIDE CORE SETTINGS ====================
SMART_RIDE_CONFIG = {
    'BASE_PRICE_PER_MINUTE': 5.0,
    'BASE_PRICE_PER_KM': 2.0,
    'SCOOTER_PRICE_MULTIPLIER': 1.0,
    'BIKE_PRICE_MULTIPLIER': 1.2,
    'MAX_RIDE_DISTANCE_KM': 50,
    'MIN_BATTERY_LEVEL': 20,
    'SUPPORT_EMAIL': 'support@smartride.com',
    'SUPPORT_PHONE': '+91-8589833473',
    'VERIFICATION_ETA_HOURS': 24,
    'SERVICE_AREA_RADIUS_KM': 10,
    'DOCUMENT_TYPES': ['aadhar_front', 'aadhar_back', 'driving_license'],
}


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

from django.contrib.staticfiles.storage import staticfiles_storage

ADMIN_CSS = 'admin/css/smartride_admin_theme.css'

def get_admin_extra_context(request):
    return {'admin_css': ADMIN_CSS}


RAZOR_KEY_ID = config("RAZOR_KEY_ID")
RAZOR_KEY_SECRET = config("RAZOR_KEY_SECRET")
RAZOR_WEBHOOK_SECRET = config("RAZOR_WEBHOOK_SECRET")
RAZORPAY_CALLBACK_URL = config("RAZORPAY_CALLBACK_URL")
