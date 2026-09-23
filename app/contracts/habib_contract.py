# app/contracts/habib_contract.py
"""
Data Contract & Interface Specification untuk Modul Habib
Dashboard Analitik (Time Series Forecasting, K-Means Clustering, NLG)

Modul ini mendefinisikan skema input/output standar yang diharapkan dari modul Habib
sehingga integrasi dengan Laravel (murialo-web) dan modul lain konsisten.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ApplicantForecastingRequest(BaseModel):
    """Permintaan perkiraan tren pelamar mendatang."""
    lowongan_id: Optional[int] = Field(None, description="Opsional filter per lowongan")
    horizon_days: int = Field(30, ge=7, le=90, description="Cakupan hari ke depan")
    historical_window_days: int = Field(90, ge=30, le=365)


class ForecastPoint(BaseModel):
    date: str
    predicted_applicants: float
    lower_bound: float
    upper_bound: float


class ApplicantForecastingResponse(BaseModel):
    status: str = "completed"
    horizon_days: int
    forecast_points: List[ForecastPoint]
    trend_summary: str = Field(..., description="Ringkasan tren deskriptif hasil NLG")
    processing_time_ms: int


class CandidateClusteringRequest(BaseModel):
    """Permintaan segmentasi kandidat menggunakan K-Means."""
    lowongan_id: Optional[int] = None
    features: List[str] = Field(
        default=["experience_years", "skill_coverage", "test_score"],
        description="Fitur yang dipakai untuk clustering"
    )
    n_clusters: int = Field(3, ge=2, le=10)


class ClusterSegment(BaseModel):
    cluster_id: int
    cluster_name: str
    candidate_ids: List[int]
    characteristics: Dict[str, Any]
    nlg_description: str = Field(..., description="Penjelasan segmen dalam bahasa alami (NLG)")


class CandidateClusteringResponse(BaseModel):
    status: str = "completed"
    n_clusters: int
    clusters: List[ClusterSegment]
    processing_time_ms: int
