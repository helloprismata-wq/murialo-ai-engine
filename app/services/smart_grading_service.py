# app/services/smart_grading_service.py
"""
Service layer untuk Smart Grading.

Baseline approach:
1. Encode jawaban kandidat dan semua jawaban acuan menggunakan S-BERT
2. Hitung cosine similarity jawaban vs setiap acuan
3. Ambil similarity tertinggi (max_reference_similarity)
4. baseline_score = clamp(max_similarity, 0, 1) × max_score
5. scoring_method = cosine_baseline, is_calibrated = false

Service ini stateless — tidak membaca/menulis database.
"""

import time
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.model_registry import get_grading_model, get_model_version
from app.services.text_processing import normalize_text, truncate_with_notice, is_blank
from app.core.config import settings

logger = logging.getLogger("murialo.smart_grading")

PIPELINE_VERSION = "1.0.0"


def compute_smart_grading(
    candidate_answer: str,
    reference_answers: list[str],
    max_score: float,
) -> dict:
    """
    Hitung baseline score untuk satu jawaban esai.

    Args:
        candidate_answer: Jawaban kandidat
        reference_answers: Daftar jawaban acuan dari HRD (minimal 1)
        max_score: Skor maksimum untuk soal ini

    Returns:
        dict berisi cosine_similarity, baseline_score, scoring_method, dll.
    """
    start_time = time.perf_counter()

    # ── Validasi input ───────────────────────────────────────────
    if not reference_answers or all(is_blank(ref) for ref in reference_answers):
        return _error_result(
            error_code="empty_reference_answers",
            error_message="Jawaban acuan tidak boleh kosong.",
            processing_time_ms=_elapsed_ms(start_time),
        )

    if max_score <= 0:
        return _error_result(
            error_code="invalid_max_score",
            error_message="Skor maksimum harus lebih besar dari 0.",
            processing_time_ms=_elapsed_ms(start_time),
        )

    # ── Jawaban kosong → skor 0, bukan error ─────────────────────
    if is_blank(candidate_answer):
        return {
            "status": "completed",
            "cosine_similarity": None,
            "max_reference_similarity": None,
            "baseline_score": 0.0,
            "predicted_score": 0.0,
            "max_score": max_score,
            "scoring_method": "cosine_baseline",
            "is_calibrated": False,
            "reason": "blank_answer",
            "model_version": get_model_version("grading"),
            "pipeline_version": PIPELINE_VERSION,
            "processing_time_ms": _elapsed_ms(start_time),
        }

    # ── Normalisasi & truncate ───────────────────────────────────
    candidate_answer = normalize_text(candidate_answer)
    candidate_answer, truncated = truncate_with_notice(
        candidate_answer, settings.MAX_INPUT_LENGTH
    )
    if truncated:
        logger.warning(f"Candidate answer truncated to {settings.MAX_INPUT_LENGTH} chars")

    # Filter reference answers yang tidak kosong
    valid_refs = [normalize_text(ref) for ref in reference_answers if not is_blank(ref)]

    # ── Encode & hitung similarity ───────────────────────────────
    model = get_grading_model()

    # Encode semua teks sekaligus: [candidate, ref1, ref2, ...]
    all_texts = [candidate_answer] + valid_refs
    embeddings = model.encode(all_texts, convert_to_numpy=True)

    candidate_vec = embeddings[0].reshape(1, -1)

    # Hitung cosine similarity terhadap setiap acuan
    similarities = []
    for i in range(1, len(embeddings)):
        ref_vec = embeddings[i].reshape(1, -1)
        sim = float(cosine_similarity(candidate_vec, ref_vec)[0][0])
        similarities.append(sim)

    # Ambil similarity tertinggi
    max_sim = max(similarities)
    clamped_sim = max(0.0, min(1.0, max_sim))

    # Baseline score
    baseline_score = round(clamped_sim * max_score, 2)

    processing_time_ms = _elapsed_ms(start_time)

    return {
        "status": "completed",
        "cosine_similarity": round(max_sim, 6),
        "max_reference_similarity": round(max_sim, 6),
        "baseline_score": baseline_score,
        "predicted_score": baseline_score,
        "max_score": max_score,
        "scoring_method": "cosine_baseline",
        "is_calibrated": False,
        "reason": None,
        "model_version": get_model_version("grading"),
        "pipeline_version": PIPELINE_VERSION,
        "processing_time_ms": processing_time_ms,
    }


def _error_result(error_code: str, error_message: str, processing_time_ms: int) -> dict:
    """Hasil error — bukan skor 0, melainkan status gagal."""
    return {
        "status": "failed",
        "cosine_similarity": None,
        "max_reference_similarity": None,
        "baseline_score": None,
        "predicted_score": None,
        "max_score": None,
        "scoring_method": "cosine_baseline",
        "is_calibrated": False,
        "reason": None,
        "error_code": error_code,
        "error_message": error_message,
        "model_version": get_model_version("grading"),
        "pipeline_version": PIPELINE_VERSION,
        "processing_time_ms": processing_time_ms,
    }


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
