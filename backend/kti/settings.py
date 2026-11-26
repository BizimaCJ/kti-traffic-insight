"""Kigali Traffic Insight - Django settings.

Configuration comes from environment variables (prefix KTI_) or a .env file next to manage.py.
The traffic thresholds are the defaults from SRS section 4.3 and can be tuned after user testing.
"""
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.environ.get(f"KTI_{name}", default)


def env_bool(name: str, default: bool) -> bool:
    return env(name, str(default)).lower() in ("1", "true", "yes", "on")


def database_from_url(url: str) -> dict:
    """Accepts postgresql://, postgresql+psycopg:// and sqlite:/// URLs."""
    if url.startswith("sqlite"):
        name = url.split("sqlite:///", 1)[-1] or ":memory:"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name if name == ":memory:" else str(BASE_DIR / name),
        }
    parsed = urlparse(url.replace("+psycopg2", "").replace("+psycopg", ""))
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
    }


SECRET_KEY = env("SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.network",
    "apps.traffic",
    "apps.incidents",
    "apps.alerts",
    "apps.audit",
    "apps.accounts",
    "apps.routing",
    "apps.simulation",
    "apps.overview",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kti.urls"
WSGI_APPLICATION = "kti.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": database_from_url(env("DATABASE_URL", "postgresql://kti:kti_dev_password@localhost:5433/kti"))
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = env("TIMEZONE", "Africa/Kigali")
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if FRONTEND_DIST.exists():  # serve the built React app (index.html is handled by the SPA view)
    WHITENOISE_ROOT = FRONTEND_DIST
    WHITENOISE_INDEX_FILE = False

# --- Administrator sessions (NFR 6): expire after inactivity, extended by activity ---
SESSION_TIMEOUT_MINUTES = int(env("SESSION_TIMEOUT_MINUTES", "15"))
SESSION_COOKIE_AGE = SESSION_TIMEOUT_MINUTES * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("SECURE_COOKIES", False)  # set KTI_SECURE_COOKIES=true behind HTTPS
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.core.authentication.AdminSessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
}

# --- Traffic rules (SRS section 4.3) ---
FREE_FLOW_MAX_DELAY = int(env("FREE_FLOW_MAX_DELAY", "2"))
MODERATE_MAX_DELAY = int(env("MODERATE_MAX_DELAY", "7"))
HEAVY_MAX_DELAY = int(env("HEAVY_MAX_DELAY", "15"))
ALERT_DELAY_THRESHOLD = int(env("ALERT_DELAY_THRESHOLD", "10"))
FREE_FLOW_SPEED_KMH = float(env("FREE_FLOW_SPEED_KMH", "30"))

# --- Abuse prevention ---
INCIDENT_REPORT_RATE = env("INCIDENT_REPORT_RATE", "5/hour")
LOGIN_RATE = env("LOGIN_RATE", "10/min")
DUPLICATE_WINDOW_MINUTES = int(env("DUPLICATE_WINDOW_MINUTES", "10"))

# --- Simulation ---
SIMULATION_SCENARIO = env("SIMULATION_SCENARIO", "auto")
SIMULATION_INTERVAL_SECONDS = int(env("SIMULATION_INTERVAL_SECONDS", "60"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
