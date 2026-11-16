"""
Configuración de Django para el Mini ERP.

Los valores sensibles (clave secreta, credenciales de MySQL) se leen
desde el archivo .env mediante python-dotenv. Ver .env.example.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env(nombre, defecto=None, requerido=False):
    valor = os.environ.get(nombre, defecto)
    if requerido and (valor is None or valor == ''):
        raise ImproperlyConfigured(f'Falta la variable de entorno {nombre} (revisa el archivo .env).')
    return valor


def env_bool(nombre, defecto=False):
    return str(env(nombre, str(defecto))).strip().lower() in ('1', 'true', 'yes', 'si', 'on')


SECRET_KEY = env('SECRET_KEY', requerido=True)
DEBUG = env_bool('DEBUG', False)
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]


# Aplicaciones

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Apps del proyecto
    'core',
    'usuarios',
    'productos',
    'clientes',
    'ventas',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Todas las vistas exigen sesión salvo las marcadas con @login_not_required
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Base de datos MySQL (credenciales en .env)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', requerido=True),
        'USER': env('DB_USER', requerido=True),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST': env('DB_HOST', '127.0.0.1'),
        'PORT': env('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'isolation_level': 'read committed',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Autenticación

AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:inicio'
LOGOUT_REDIRECT_URL = 'login'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True


# Internacionalización

LANGUAGE_CODE = 'es'
TIME_ZONE = env('TIME_ZONE', 'America/Bogota')
USE_I18N = True
USE_TZ = True


# Archivos estáticos

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Mensajes con clases de Bootstrap

from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}


# Email (consola en desarrollo)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
