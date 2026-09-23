# app/core/config.py
"""
Konfigurasi terpusat untuk Murialo AI Engine.
Menggunakan Pydantic BaseSettings agar bisa dibaca dari .env atau environment variables.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


# Root proyek = parent dari folder app/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Konfigurasi AI Engine. Semua nilai bisa di-override via .env atau env vars."""

    # ── Server ───────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False

    # ── Keamanan ─────────────────────────────────────────────────
    AI_API_KEY: str = ""

    # ── Model Paths ──────────────────────────────────────────────
    MATCHING_MODEL_PATH: str = str(PROJECT_ROOT / "models" / "sbert-murialo")
    GRADING_MODEL_NAME_OR_PATH: str = str(PROJECT_ROOT / "models" / "sbert-murialo")
    MODEL_DEVICE: str = "cpu"

    # ── Batas Input ──────────────────────────────────────────────
    MAX_INPUT_LENGTH: int = 50_000       # karakter
    MAX_BATCH_SIZE: int = 20
    MAX_REFERENCE_ANSWERS: int = 10
    MAX_SKILLS_COUNT: int = 100

    # ── Concurrency ──────────────────────────────────────────────
    MODEL_MAX_CONCURRENCY: int = 2       # semaphore untuk embedding calls

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton — diimpor oleh modul lain
settings = Settings()
