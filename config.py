# config.py
from __future__ import annotations
import os
import pathlib
from urllib.parse import quote_plus

BASE_DIR = pathlib.Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if (v is not None and str(v).strip() != "") else default

# --- Configuration MySQL ---
DB_HOST = env("DB_HOST", "127.0.0.1")
DB_PORT = env("DB_PORT", "3306")
DB_NAME = env("DB_NAME", "madargn")
DB_USER = env("DB_USER", "root")
DB_PASSWORD_RAW = env("DB_PASSWORD", "Z@291721Gn@")

# Encodage sûr
DB_PASSWORD = quote_plus(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else ""

# DATABASE_URL > DB_* > fallback SQLite
# Supporte MySQL, PostgreSQL et SQLite
_database_url = env("DATABASE_URL")
if _database_url:
    # Render fournit DATABASE_URL pour PostgreSQL (postgresql://...)
    # Convertir postgresql:// en postgresql+psycopg2:// si nécessaire
    if _database_url.startswith("postgresql://") and "psycopg2" not in _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = _database_url
elif DB_NAME:  # MySQL
    auth = f"{DB_USER}:{DB_PASSWORD}@" if DB_PASSWORD_RAW else f"{DB_USER}@"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{auth}{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
else:  # Fallback SQLite
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR/'app.db'}"

def engine_options_for(uri: str) -> dict:
    is_mysql = uri.startswith("mysql+pymysql://")
    is_postgresql = uri.startswith("postgresql://") or uri.startswith("postgresql+psycopg2://")
    opts = {"pool_pre_ping": True}
    if is_mysql or is_postgresql:
        opts.update({
            "pool_size": int(env("DB_POOL_SIZE", "5")),
            "max_overflow": int(env("DB_MAX_OVERFLOW", "10")),
            "pool_recycle": int(env("DB_POOL_RECYCLE", "280")),
        })
    return opts

class Config:
    SECRET_KEY = env("SECRET_KEY", "import_profit_pro_2024")
    DEBUG = env("FLASK_DEBUG", "1") == "1"

    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = env("SQLALCHEMY_ECHO", "0") == "1"
    SQLALCHEMY_ENGINE_OPTIONS = engine_options_for(SQLALCHEMY_DATABASE_URI)

    BASE_DIR = BASE_DIR
    INSTANCE_DIR = INSTANCE_DIR
    UPLOAD_FOLDER = str(INSTANCE_DIR / "uploads")
    pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

    MAX_CONTENT_LENGTH = int(env("MAX_CONTENT_MB", "25")) * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    JSON_SORT_KEYS = False
    PREFERRED_URL_SCHEME = env("URL_SCHEME", "http")
    
    # Configuration Email (Flask-Mail)
    MAIL_SERVER = env("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(env("MAIL_PORT", "587"))
    MAIL_USE_TLS = env("MAIL_USE_TLS", "1") == "1"
    MAIL_USE_SSL = env("MAIL_USE_SSL", "0") == "1"
    MAIL_USERNAME = env("MAIL_USERNAME")
    MAIL_PASSWORD = env("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = env("MAIL_DEFAULT_SENDER", env("MAIL_USERNAME"))
    MAIL_SUPPRESS_SEND = env("MAIL_SUPPRESS_SEND", "0") == "1"  # Pour les tests

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
