# app/contracts/raka_contract.py
"""
Data Contract & Interface Specification untuk Modul Raka
Rekomendasi Kandidat (Collaborative Filtering & Content-Based Filtering)

Modul ini mendefinisikan skema input/output standar yang diharapkan dari modul Raka
sehingga integrasi dengan Laravel (murialo-web) dan modul lain konsisten.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CandidateRecommendationRequest(BaseModel):
    """Permintaan rekomendasi kandidat untuk suatu lowongan tertentu."""
    lowongan_id: int = Field(..., description="ID lowongan pekerjaan")
    top_k: int = Field(10, ge=1, le=50, description="Jumlah maksimal rekomendasi yang dikembalikan")
    method: str = Field(
        "hybrid",
        description="Metode filtering: 'content_based', 'collaborative', atau 'hybrid'"
    )
    filter_criteria: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter tambahan seperti min_pendidikan, domisili, atau ketersediaan"
    )


class RecommendedCandidateItem(BaseModel):
    """Item kandidat hasil rekomendasi."""
    pelamar_id: int
    user_id: Optional[int] = None
    nama: str
    compatibility_score: float = Field(..., ge=0.0, le=100.0, description="Skor kecocokan (0-100)")
    ranking: int = Field(..., ge=1)
    recommendation_reason: Optional[str] = Field(
        None,
        description="Penjelasan ringkas mengapa kandidat direkomendasikan"
    )
    matched_features: List[str] = Field(default_factory=list)


class CandidateRecommendationResponse(BaseModel):
    """Respons rekomendasi kandidat dari AI engine."""
    status: str = "completed"
    lowongan_id: int
    method_used: str
    total_candidates_evaluated: int
    recommendations: List[RecommendedCandidateItem]
    model_version: Optional[str] = None
    processing_time_ms: int
