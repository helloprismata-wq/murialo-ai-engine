# app/schemas/smart_grading.py
"""
Pydantic schemas untuk endpoint Smart Grading.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid
from typing import Optional, Union

# ── Request ──────────────────────────────────────────────────────

class SmartGradingRequest(BaseModel):
    """Request untuk single smart grading."""
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="ID unik request dari Laravel")
    candidate_id: Optional[Union[str, int]] = Field(None, description="ID kandidat di Laravel")
    attempt_id: Optional[Union[str, int]] = Field(None, description="ID percobaan tes")
    answer_id: Optional[Union[str, int]] = Field(None, description="ID jawaban kandidat di Laravel")
    answer_version: Optional[str] = Field(None, description="Hash/versi jawaban")
    question_id: Optional[Union[str, int]] = Field(None, description="ID soal di Laravel")
    question_version: Optional[int] = Field(None, description="Versi soal saat snapshot")
    candidate_answer: str = Field(..., max_length=50_000, description="Jawaban esai kandidat")
    reference_answers: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Daftar jawaban acuan dari HRD",
    )
    max_score: float = Field(..., gt=0, description="Skor maksimum soal")

    @field_validator("reference_answers")
    @classmethod
    def at_least_one_non_empty(cls, v: list[str]) -> list[str]:
        if not any(ref.strip() for ref in v):
            raise ValueError("Minimal satu jawaban acuan harus berisi teks.")
        return v


class SmartGradingBatchRequest(BaseModel):
    """Request untuk batch smart grading."""
    items: list[SmartGradingRequest] = Field(..., min_length=1, max_length=20)


# ── Response ─────────────────────────────────────────────────────

class SmartGradingResult(BaseModel):
    """Hasil grading satu jawaban esai."""
    schema_version: str = "1.0"
    request_id: str
    candidate_id: Optional[Union[str, int]] = None
    attempt_id: Optional[Union[str, int]] = None
    answer_id: Optional[Union[str, int]] = None
    question_id: Optional[Union[str, int]] = None
    question_version: Optional[int] = None
    status: str  # completed | failed
    cosine_similarity: Optional[float] = None
    max_reference_similarity: Optional[float] = None
    baseline_score: Optional[float] = None
    predicted_score: Optional[float] = None
    max_score: Optional[float] = None
    scoring_method: str = "cosine_baseline"
    is_calibrated: bool = False
    reason: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    model_version: str = ""
    pipeline_version: str = ""
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0


class SmartGradingResponse(BaseModel):
    """Wrapper response untuk single grading."""
    data: SmartGradingResult


class SmartGradingBatchResponse(BaseModel):
    """Wrapper response untuk batch grading."""
    data: list[SmartGradingResult]
    total: int
    completed: int
    failed: int
