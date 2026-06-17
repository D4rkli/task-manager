import dj_database_url
from pathlib import Path
from django.core.management.utils import get_random_secret_key

import secrets
from django.core.exceptions import ImproperlyConfigured
import rollbar
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)

def env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name, str(default))
    return val.lower() in {"1", "true", "yes", "y", "on"}


DEBUG = env_flag("DJANGO_DEBUG", False)

_secret = os.getenv("DJANGO_SECRET_KEY")
if not _secret:
    if env_flag("CI", False):
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is not set")
    _secret = get_random_secret_key()
SECRET_KEY = _secret

_default_hosts = "webserver,localhost,127.0.0.1"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",")
    if h.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'task_manager',
    'task_manager.tasks',
    'task_manager.labels',
    'task_manager.users',
    'task_manager.statuses',
    'django_filters',
    'django_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'task_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "task_manager" / "templates",
        ],
        'APP_DIRS': True,
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

WSGI_APPLICATION = "task_manager.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        ssl_require=True,
    )
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
}

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/login/"


def rollbar_person(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return {"id": user.id, "username": user.username, "email": user.email}
    return None

ROLLBAR = {
    "access_token": os.getenv("ROLLBAR_ACCESS_TOKEN", "").strip(),
    "environment": os.getenv("ROLLBAR_ENV", "development"),
    "root": str(BASE_DIR),
    "code_version": os.getenv("GIT_COMMIT", "").strip(),
    "capture_ip": "anonymize",
    "person_fn": "task_manager.settings.rollbar_person",
    "scrub_fields": ["password", "secret", "token"],
}

if ROLLBAR["access_token"]:
    rollbar.init(**ROLLBAR)

render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)

extra = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS += [h.strip() for h in extra.split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = []
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

extra_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS += [u.strip() for u in extra_csrf.split(",") if u.strip()]
