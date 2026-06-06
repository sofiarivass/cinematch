"""
config/config.py
────────────────
Configuración centralizada de la aplicación.
Lee las variables de entorno desde el archivo .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY   = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG        = os.getenv("FLASK_DEBUG", "True") == "True"

    # ── TMDB ──────────────────────────────────────────────────────────────
    TMDB_API_KEY        = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL       = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    TMDB_LANGUAGE       = "es-MX"