import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _  # 🌐 Translation Engine

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-s56+j*3^rrsy2==$4mjw#e-^%mqtc&&jab^df*kt5uge9q6k^*'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # 🌐 Multi-language engine (MUST be after SessionMiddleware)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # 🌐 Exposes language context to templates
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
# 🛰️ Enable the asynchronous server gateway interface routing matrix
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mobile_shop_db',
        'USER': 'postgres',
        'PASSWORD': '20041807',  # Update with your password!
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==========================================
# 🌐 INTERNATIONALIZATION & MULTI-LANGUAGE
# ==========================================

LANGUAGE_CODE = 'en'  # Default Language

LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
    ('ky', _('Kyrgyz')),
]

# Directory where translation files (.po / .mo) will be stored
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ==========================================
# 📁 MEDIA & STATIC FILES
# ==========================================

STATIC_URL = 'static/'

# Base url to serve media files
MEDIA_URL = '/media/'

# Path where media files are physically stored on your computer
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Session key for the shopping cart
CART_SESSION_ID = 'techvault_cart'


# ==========================================
# 📑 DRF & API DOCUMENTATION SETTINGS
# ==========================================

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TechVault Core E-Commerce API',
    'DESCRIPTION': 'Core API catalog for products, categories, and inventory management.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# 🏎️ LOCAL RECONFIGURED CACHING INFRASTRUCTURE (For running without Docker)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'techvault_cache_table',
    }
}

# ==========================================
# ⚡ CELERY & REDIS TASK QUEUE SETTINGS
# ==========================================

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Force Redis driver to use RESP2 protocol to prevent HELLO command errors
CELERY_BROKER_TRANSPORT_OPTIONS = {'protocol_version': 2}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'