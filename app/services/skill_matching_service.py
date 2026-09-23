# app/services/skill_matching_service.py
"""
Service layer untuk Skill Matching.

Alur:
1. Encode resume_text dan job_description menggunakan S-BERT → cosine similarity
2. Cocokkan required_skills terhadap resume_text (exact + alias)
3. Kembalikan skor similarity, matched/not_found skills, dan coverage

Service ini stateless — tidak membaca/menulis database.
"""

import time
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.model_registry import get_matching_model, get_model_version
from app.services.text_processing import normalize_text, truncate_with_notice, is_blank
from app.services.skill_normalization import match_skill_in_text
from app.core.config import settings

logger = logging.getLogger("murialo.skill_matching")

PIPELINE_VERSION = "1.0.0"


def compute_skill_matching(
    resume_text: str,
    job_description: str,
    candidate_skills: list[str] | None = None,
    required_skills: list[str] | None = None,
) -> dict:
    """
    Hitung skill matching antara resume pelamar dan deskripsi lowongan.

    Args:
        resume_text: Teks CV / resume pelamar
        job_description: Teks deskripsi + kualifikasi lowongan
        candidate_skills: Skill eksplisit kandidat (opsional, dari parser)
        required_skills: Skill yang dibutuhkan lowongan

    Returns:
        dict berisi cosine_similarity, similarity_score, matched_skills, dll.
    """
    start_time = time.perf_counter()

    # Normalisasi input
    resume_text = normalize_text(resume_text)
    job_description = normalize_text(job_description)

    if is_blank(resume_text) or is_blank(job_description):
        return _empty_result(
            reason="Input kosong",
            processing_time_ms=_elapsed_ms(start_time),
        )

    # Truncate jika terlalu panjang
    resume_text, resume_truncated = truncate_with_notice(resume_text, settings.MAX_INPUT_LENGTH)
    job_description, job_truncated = truncate_with_notice(job_description, settings.MAX_INPUT_LENGTH)

    if resume_truncated:
        logger.warning(f"Resume text truncated to {settings.MAX_INPUT_LENGTH} chars")
    if job_truncated:
        logger.warning(f"Job description truncated to {settings.MAX_INPUT_LENGTH} chars")

    # ── Cosine Similarity ────────────────────────────────────────
    model = get_matching_model()
    embeddings = model.encode([resume_text, job_description], convert_to_numpy=True)
    resume_vec = embeddings[0].reshape(1, -1)
    job_vec = embeddings[1].reshape(1, -1)

    cosine_raw = float(cosine_similarity(resume_vec, job_vec)[0][0])
    similarity_score = round(max(0.0, min(100.0, cosine_raw * 100.0)), 2)

    # ── Skill Gap Analysis ───────────────────────────────────────
    matched_skills = []
    not_found_skills = []

    # Gunakan candidate_skills jika tersedia, fallback ke resume_text
    search_text = resume_text
    if candidate_skills:
        search_text = resume_text + " " + " ".join(candidate_skills)

    if required_skills:
        for skill in required_skills:
            skill = skill.strip()
            if not skill:
                continue
            found, method = match_skill_in_text(skill, search_text)
            if found:
                matched_skills.append({
                    "skill": skill,
                    "match_method": method,  # 'exact' atau 'alias'
                })
            else:
                not_found_skills.append({
                    "skill": skill,
                    "note": "Tidak ditemukan secara eksplisit di input. Bukan berarti kandidat tidak memilikinya.",
                })

    total_required = len(matched_skills) + len(not_found_skills)
    skill_coverage = round((len(matched_skills) / total_required * 100), 1) if total_required > 0 else None

    processing_time_ms = _elapsed_ms(start_time)

    return {
        "status": "completed",
        "cosine_similarity": round(cosine_raw, 6),
        "similarity_score": similarity_score,
        "scoring_method": "cosine_sbert",
        "matched_skills": matched_skills,
        "not_found_skills": not_found_skills,
        "skill_coverage": skill_coverage,
        "model_version": get_model_version("matching"),
        "pipeline_version": PIPELINE_VERSION,
        "processing_time_ms": processing_time_ms,
        "input_truncated": resume_truncated or job_truncated,
    }


def _empty_result(reason: str, processing_time_ms: int) -> dict:
    """Hasil kosong untuk input invalid."""
    return {
        "status": "completed",
        "cosine_similarity": None,
        "similarity_score": 0.0,
        "scoring_method": "cosine_sbert",
        "matched_skills": [],
        "not_found_skills": [],
        "skill_coverage": None,
        "model_version": get_model_version("matching"),
        "pipeline_version": PIPELINE_VERSION,
        "processing_time_ms": processing_time_ms,
        "input_truncated": False,
        "note": reason,
    }


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
