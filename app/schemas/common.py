# app/schemas/common.py
"""
Schema umum yang dipakai lintas modul.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any


class ErrorResponse(BaseModel):
    """Respons error terstruktur."""
    error: str = Field(..., description="Kode error")
    message: str = Field(..., description="Pesan error untuk developer")
    request_id: Optional[str] = None
    details: Optional[Any] = None


class HealthResponse(BaseModel):
    """Respons health check."""
    status: str
    models_loaded: bool = False
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
