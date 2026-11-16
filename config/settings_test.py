"""
Configuración para ejecutar las pruebas SIN MySQL (SQLite en memoria).

Uso:
    python manage.py test --settings=config.settings_test

No requiere credenciales: si el .env no define SECRET_KEY o los datos de la
base, se usan valores de prueba. La prueba de concurrencia de ventas se omite
automáticamente porque necesita MySQL (SELECT ... FOR UPDATE).
"""

import os

os.environ.setdefault('SECRET_KEY', 'clave-solo-para-pruebas')
os.environ.setdefault('DB_NAME', 'sin_uso')
os.environ.setdefault('DB_USER', 'sin_uso')

from .settings import *  # noqa: E402,F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Hash rápido para acelerar las pruebas (nunca usar en producción).
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
