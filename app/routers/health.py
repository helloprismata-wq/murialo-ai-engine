# app/routers/health.py
"""
Health check endpoints untuk monitoring dan orchestration.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

from app.core.model_registry import is_ready, get_matching_model, get_grading_model
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def liveness():
    """Liveness probe — server berjalan."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness():
    """Readiness probe — server siap menerima request (model sudah dimuat)."""
    models_ok = is_ready()
    return {
        "status": "ready" if models_ok else "not_ready",
        "models_loaded": models_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/v1/health")
def health_v1():
    """Endpoint status API v1."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/v1/health/detailed")
def health_detailed():
    """Detailed health check termasuk status model."""
    models_ok = is_ready()
    return {
        "status": "ok" if models_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": {
            "loaded": models_ok,
            "matching_model": settings.MATCHING_MODEL_PATH,
            "grading_model": settings.GRADING_MODEL_NAME_OR_PATH,
            "device": settings.MODEL_DEVICE,
        }
    }
