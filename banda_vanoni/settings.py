"""
Django settings for banda_vanoni project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-0#e#e&=6(alij87)j#73ik)w#&mfnx9*q5#kmz91-r@s0)d14a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['randyp107.pythonanywhere.com', 'localhost','127.0.0.1']


# Application definition
INSTALLED_APPS = [
    'admin_material.apps.AdminMaterialDashboardConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Apps externas
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'channels',
    'rest_framework',

    # Apps del proyecto - 
    'dashboard',
    "clientes",
    "proveedores",
    "productos",
    "inventario",
    "adquisiciones",
    "pedidos",
    "facturacion",

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'banda_vanoni.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'banda_vanoni.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
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



LANGUAGE_CODE = 'es-es'  
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True



STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGIN_REDIRECT_URL = '/'  
LOGOUT_REDIRECT_URL = '/admin/login/'  
LOGIN_URL = '/admin/login/'  


ASGI_APPLICATION = "banda_vanoni.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}


ADMIN_SITE_HEADER = "Sistema Banda Vanoni"
ADMIN_SITE_TITLE = "Dashboard Empresarial"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('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', '')  
DEFAULT_FROM_EMAIL = 'randypenaherrera42@gmail.com'
SITE_NAME = 'Banda Vanoni Cia. Ltda.'

