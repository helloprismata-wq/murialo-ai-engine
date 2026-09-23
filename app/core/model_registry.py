# app/core/model_registry.py
"""
Singleton model loader menggunakan FastAPI lifespan.

Model dimuat SEKALI saat startup dan dibagikan ke seluruh request.
Mendukung model matching dan grading yang bisa berbeda.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger("murialo.model_registry")

# ── Variabel internal ────────────────────────────────────────────
_matching_model: Optional[SentenceTransformer] = None
_grading_model: Optional[SentenceTransformer] = None
_model_versions: dict[str, str] = {}

# Semaphore untuk membatasi concurrent embedding calls
_semaphore: Optional[asyncio.Semaphore] = None


def _resolve_path(path_str: str) -> str:
    """Resolve path relatif terhadap project root."""
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    from app.core.config import PROJECT_ROOT
    resolved = PROJECT_ROOT / p
    return str(resolved)


def load_models() -> None:
    """
    Muat semua model ke memori. Dipanggil sekali dari FastAPI lifespan.
    Jika matching dan grading menunjuk model yang sama, gunakan instance yang sama.
    """
    global _matching_model, _grading_model, _semaphore

    matching_path = _resolve_path(settings.MATCHING_MODEL_PATH)
    grading_path = _resolve_path(settings.GRADING_MODEL_NAME_OR_PATH)

    logger.info(f"Loading matching model from: {matching_path}")
    _matching_model = SentenceTransformer(matching_path, device=settings.MODEL_DEVICE)
    _model_versions["matching"] = matching_path
    logger.info("Matching model loaded successfully.")

    if grading_path == matching_path:
        logger.info("Grading model same as matching — sharing instance.")
        _grading_model = _matching_model
        _model_versions["grading"] = matching_path
    else:
        logger.info(f"Loading grading model from: {grading_path}")
        _grading_model = SentenceTransformer(grading_path, device=settings.MODEL_DEVICE)
        _model_versions["grading"] = grading_path
        logger.info("Grading model loaded successfully.")

    _semaphore = asyncio.Semaphore(settings.MODEL_MAX_CONCURRENCY)


def get_matching_model() -> SentenceTransformer:
    """Kembalikan model untuk skill matching. Raise jika belum di-load."""
    if _matching_model is None:
        raise RuntimeError("Matching model belum dimuat. Pastikan server sudah startup dengan benar.")
    return _matching_model


def get_grading_model() -> SentenceTransformer:
    """Kembalikan model untuk smart grading. Raise jika belum di-load."""
    if _grading_model is None:
        raise RuntimeError("Grading model belum dimuat. Pastikan server sudah startup dengan benar.")
    return _grading_model


def get_model_version(model_type: str = "matching") -> str:
    """Kembalikan path/nama model yang sedang aktif."""
    return _model_versions.get(model_type, "unknown")


def get_semaphore() -> asyncio.Semaphore:
    """Kembalikan semaphore untuk rate limiting embedding calls."""
    if _semaphore is None:
        return asyncio.Semaphore(settings.MODEL_MAX_CONCURRENCY)
    return _semaphore


def is_ready() -> bool:
    """Cek apakah semua model sudah dimuat."""
    return _matching_model is not None and _grading_model is not None
