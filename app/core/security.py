# app/core/security.py
"""
Autentikasi layanan via header X-API-Key.
Dipakai sebagai FastAPI dependency pada router yang perlu dilindungi.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """
    Verifikasi API key dari header request.
    Jika AI_API_KEY tidak dikonfigurasi (kosong), autentikasi dilewati (dev mode).
    """
    # Jika API key belum diset di server, skip auth (development)
    if not settings.AI_API_KEY:
        return "dev-no-key"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_api_key", "message": "Header X-API-Key wajib disertakan."},
        )

    if api_key != settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "message": "API key tidak valid."},
        )

    return api_key
