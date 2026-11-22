"""Django settings for Zuza's Manager.

All environment-specific values come from environment variables. A `.env` file in the
project root is loaded automatically (see `.env.example`).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Variables already set in the environment win over .env (python-dotenv never overrides);
# compose.verify.yaml relies on that to switch real e-mail off.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off.")
    SECRET_KEY = "insecure-dev-only-key"  # noqa: S105 – dev fallback, rejected when DEBUG is off

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# The app is served only over plain HTTP on localhost (no TLS), so HTTPS-only settings
# would break it. Revisit if the app ever runs on a server (docs/decisions.md #19).
SILENCED_SYSTEM_CHECKS = [
    "security.W004",  # SECURE_HSTS_SECONDS
    "security.W008",  # SECURE_SSL_REDIRECT
    "security.W012",  # SESSION_COOKIE_SECURE
    "security.W016",  # CSRF_COOKIE_SECURE
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "dashboard",
    "employees",
    "backups",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # whitenoise serves collected static files in production; runserver serves them in DEBUG.
    *([] if DEBUG else ["whitenoise.middleware.WhiteNoiseMiddleware"]),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.hotel_links",
                "backups.context_processors.backup_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}


# Authentication

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# The login expires 24 hours after the last activity.
SESSION_COOKIE_AGE = 24 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True


# Internationalization

LANGUAGE_CODE = "cs"
TIME_ZONE = "Europe/Prague"
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Logging – everything to the console, i.e. `docker compose logs`. Django's default
# drops errors when DEBUG is off (it only mails ADMINS, which this app has none of),
# so a crash on Zuza's laptop would leave no traceback anywhere.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        # ERROR, not WARNING: 4xx responses are logged as warnings and are just noise here.
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}


# E-mail – used only for backups, always sent through the app's own Gmail account
# (docs/decisions.md #12). Without the app password, e-mails are only printed to the log.

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "zuzasmanager@gmail.com"
# Google shows app passwords with spaces ("abcd efgh ..."); accept them as pasted.
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").replace(" ", "")
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_TIMEOUT = 30
DEFAULT_FROM_EMAIL = f"Zuza’s Manager <{EMAIL_HOST_USER}>"

# Recipients of the backup e-mail (comma-separated).
BACKUP_EMAIL_TO = env_list("BACKUP_EMAIL_TO", "")


# Hotel links shown in the header (label, URL, Bootstrap Icons class).

HOTEL_LINKS = [
    {"label": "Web hotelu", "url": "https://hotelschreiner.cz/", "icon": "bi-globe2"},
    {
        "label": "Facebook",
        "url": "https://www.facebook.com/schreinerhotel",
        "icon": "bi-facebook",
    },
    {
        "label": "Instagram",
        "url": "https://www.instagram.com/hotelschreiner/",
        "icon": "bi-instagram",
    },
]
