from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables del archivo .env automaticamente
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass  # Si no esta instalado, usa variables del sistema


def _env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# Seguridad/configuración
DEBUG = _env('DJANGO_DEBUG', 'True') == 'True'
SECRET_KEY = _env(
    'DJANGO_SECRET_KEY',
    # Solo para desarrollo local. En producción es obligatorio usar variable.
    'dev-only-change-me',
    required=not DEBUG,
)
ALLOWED_HOSTS = [host.strip() for host in _env('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if host.strip()]

INSTALLED_APPS = [
    'app',
    'usuarios', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'app' / 'templates',
            BASE_DIR / 'usuarios' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.notificaciones',  
                
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': _env('DB_NAME', 'proyecto'),
        'USER': _env('DB_USER', 'root'),
        'PASSWORD': _env('DB_PASSWORD', '123456',),
        'HOST': _env('DB_HOST', 'localhost'),
        'PORT': _env('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET time_zone = '-05:00'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'app' / 'static']

# ── Archivos subidos por el usuario (fotos de admins, etc.) ──────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email: SMTP real siempre
# Las credenciales DEBEN venir del archivo .env en producción.
_email_user     = _env('EMAIL_HOST_USER',     '')
_email_password = _env('EMAIL_HOST_PASSWORD', '')
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = _env('EMAIL_HOST',     'smtp.gmail.com')
EMAIL_PORT          = int(_env('EMAIL_PORT', 587))
EMAIL_USE_TLS       = _env('EMAIL_USE_TLS',  'True') == 'True'
EMAIL_HOST_USER     = _email_user
EMAIL_HOST_PASSWORD = _email_password
DEFAULT_FROM_EMAIL  = _env('DEFAULT_FROM_EMAIL', _email_user or 'no-reply@localhost')
EMAIL_TIMEOUT       = int(_env('EMAIL_TIMEOUT',  10))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'