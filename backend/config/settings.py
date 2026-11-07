"""
CampusFix Django settings.

Everything environment-specific (secret key, database, origins, cookie
security, upload limits) is read from environment variables / a local .env file.
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-development-only-key"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is False.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# ---------------------------------------------------------------- Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "corsheaders",
    "django_filters",
    # CampusFix apps
    "apps.departments",
    "apps.accounts",
    "apps.tickets",
    "apps.dashboard",
    "apps.django_demo",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------------------------------------------------- Database
if not os.environ.get("DATABASE_URL"):
    raise ImproperlyConfigured(
        "DATABASE_URL is not set. Copy backend/.env.example to backend/.env and edit it."
    )
DATABASES = {"default": dj_database_url.config(env="DATABASE_URL", conn_max_age=60)}

# ------------------------------------------------------------ Users / passwords
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

import sys  # noqa: E402

if "test" in sys.argv:
    # Speeds up the test suite only; production keeps Django's strong default hasher.
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LOGIN_URL = "/demo/login/"
LOGIN_REDIRECT_URL = "/demo/"
LOGOUT_REDIRECT_URL = "/demo/"

# ------------------------------------------------------------- I18N / time zone
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------- Static / media files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "media"))
if not MEDIA_ROOT.is_absolute():
    MEDIA_ROOT = BASE_DIR / MEDIA_ROOT
# NOTE: MEDIA_URL is intentionally NOT routed. Attachments are only served by the
# permission-checked API endpoint, never as public static files.
MEDIA_URL = "media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------- Sessions, CSRF and CORS
SESSION_COOKIE_AGE = int(os.environ.get("SESSION_COOKIE_AGE", 8 * 60 * 60))
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
CSRF_COOKIE_SAMESITE = "Lax"

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]  # exact origin only - no wildcard with credentials
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", FRONTEND_ORIGIN)

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ------------------------------------------------------------ REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.SessionAuthentication401"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_RATES": {"login": os.environ.get("LOGIN_THROTTLE_RATE", "30/min")},
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

# ------------------------------------------------------------------- Uploads
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))
# Allow-list: Pillow format name -> (content type, stored extension). Sample values.
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
    "GIF": ("image/gif", ".gif"),
}

# ----------------------------------------------------------- SLA configuration
# SINGLE place for response / resolution targets (elapsed calendar hours).
# These are SAMPLE values for the demonstration - the real durations are still
# "TBD" in the requirements and must be agreed before any real use.
SLA_TARGETS = {
    "LOW": {"response_hours": 24, "resolution_hours": 120},
    "MEDIUM": {"response_hours": 8, "resolution_hours": 72},
    "HIGH": {"response_hours": 4, "resolution_hours": 24},
    "URGENT": {"response_hours": 1, "resolution_hours": 8},
}
SLA_DUE_SOON_HOURS = 4  # "approaching deadline" window on the staff dashboard

# --------------------------------------------------------------------- Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}
