"""
Router - Modul Rekomendasi Kandidat
Murialo - Satyatma Raka Wiratama

Endpoint API buat modul rekomendasi kandidat, ikutin pola yang sama
kayak app/routers/resume_parser.py (Khamdanul).

Logic-nya ada di app/services/recommendation.py - file ini cuma
bagian endpoint/routing-nya aja.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services.recommendation import (
    kandidat_dummy,
    lowongan_dummy,
    histori_interaksi_dummy,
    recommend_candidates_gabungan,
)

router = APIRouter()


# ---------------------------------------------------------
# SCHEMA RESPONSE (biar bentuk output-nya jelas & konsisten)
# ---------------------------------------------------------

class RekomendasiKandidat(BaseModel):
    kandidat_id: str
    nama: str
    skor_content_based: float
    skor_collaborative: float
    skor_akhir: float


class RekomendasiResponse(BaseModel):
    lowongan_id: str
    posisi: str
    rekomendasi: List[RekomendasiKandidat]


# ---------------------------------------------------------
# ENDPOINT
# ---------------------------------------------------------

@router.get("/")
def rekomendasi_status():
    """Cek status modul - sama kayak pola resume-parser."""
    return {"module": "rekomendasi-kandidat", "status": "ready"}


@router.get("/{lowongan_id}", response_model=RekomendasiResponse)
def get_rekomendasi(lowongan_id: str, top_n: int = 3):
    """
    Ambil daftar kandidat yang direkomendasikan untuk satu lowongan.

    Contoh: GET /rekomendasi-kandidat/L001?top_n=3
    """
    lowongan = next(
        (l for l in lowongan_dummy if l["lowongan_id"] == lowongan_id), None
    )
    if not lowongan:
        raise HTTPException(status_code=404, detail=f"Lowongan {lowongan_id} tidak ditemukan")

    hasil = recommend_candidates_gabungan(
        lowongan,
        kandidat_dummy,
        lowongan_dummy,
        histori_interaksi_dummy,
        top_n=top_n,
    )

    return {
        "lowongan_id": lowongan["lowongan_id"],
        "posisi": lowongan["posisi"],
        "rekomendasi": hasil,
    }