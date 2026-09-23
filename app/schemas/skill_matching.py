# app/schemas/skill_matching.py
"""
Pydantic schemas untuk endpoint Skill Matching.
"""

from datetime import datetime
from pydantic import BaseModel, Field
import uuid
from typing import Optional, Union

# ── Request ──────────────────────────────────────────────────────

class SkillMatchingRequest(BaseModel):
    """Request untuk single skill matching."""
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="ID unik request dari Laravel")
    candidate_id: Optional[Union[str, int]] = Field(None, description="ID kandidat di Laravel")
    job_id: Optional[Union[str, int]] = Field(None, description="ID lowongan di Laravel")
    input_version: Optional[str] = Field(None, description="Hash/versi snapshot input")
    resume_text: str = Field(..., min_length=1, max_length=50_000, description="Teks CV / resume")
    job_description: str = Field(..., min_length=1, max_length=50_000, description="Deskripsi lowongan")
    candidate_skills: Optional[list[str]] = Field(None, description="Skill eksplisit kandidat (dari parser)")
    required_skills: Optional[list[str]] = Field(None, description="Skill yang dibutuhkan lowongan")


class SkillMatchingBatchRequest(BaseModel):
    """Request untuk batch skill matching."""
    items: list[SkillMatchingRequest] = Field(..., min_length=1, max_length=20)


# ── Response ─────────────────────────────────────────────────────

class MatchedSkill(BaseModel):
    """Detail satu skill yang cocok."""
    skill: str
    match_method: str  # exact | alias


class NotFoundSkill(BaseModel):
    """Detail satu skill yang tidak ditemukan."""
    skill: str
    note: str


class SkillMatchingResult(BaseModel):
    """Hasil matching satu pasang resume-lowongan."""
    schema_version: str = "1.0"
    request_id: str
    candidate_id: Optional[Union[str, int]] = None
    job_id: Optional[Union[str, int]] = None
    input_version: Optional[str] = None
    status: str  # completed | failed
    cosine_similarity: Optional[float] = None
    similarity_score: float = 0.0
    scoring_method: str = "cosine_sbert"
    matched_skills: list[MatchedSkill] = []
    not_found_skills: list[NotFoundSkill] = []
    skill_coverage: Optional[float] = None
    model_version: str = ""
    pipeline_version: str = ""
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0
    input_truncated: bool = False
    note: Optional[str] = None


class SkillMatchingResponse(BaseModel):
    """Wrapper response untuk single matching."""
    data: SkillMatchingResult


class SkillMatchingBatchResponse(BaseModel):
    """Wrapper response untuk batch matching."""
    data: list[SkillMatchingResult]
    total: int
    completed: int
    failed: int
