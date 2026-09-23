# app/routers/skill_matching.py
"""
Router untuk endpoint Skill Matching.
Semua endpoint memerlukan API key (jika dikonfigurasi).
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import verify_api_key
from app.core.config import settings
from app.schemas.skill_matching import (
    SkillMatchingRequest,
    SkillMatchingBatchRequest,
    SkillMatchingResponse,
    SkillMatchingBatchResponse,
    SkillMatchingResult,
    MatchedSkill,
    NotFoundSkill,
)
from app.services.skill_matching_service import compute_skill_matching

logger = logging.getLogger("murialo.router.skill_matching")

router = APIRouter(
    prefix="/api/v1",
    tags=["Skill Matching"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/skill-matching", response_model=SkillMatchingResponse)
async def skill_matching(req: SkillMatchingRequest):
    """
    Hitung skill matching antara resume kandidat dan deskripsi lowongan.

    Input dikirim oleh backend Laravel — browser kandidat TIDAK memanggil endpoint ini.
    """
    try:
        raw = compute_skill_matching(
            resume_text=req.resume_text,
            job_description=req.job_description,
            candidate_skills=req.candidate_skills,
            required_skills=req.required_skills,
        )

        result = SkillMatchingResult(
            request_id=req.request_id,
            candidate_id=req.candidate_id,
            job_id=req.job_id,
            input_version=req.input_version,
            status=raw["status"],
            cosine_similarity=raw["cosine_similarity"],
            similarity_score=raw["similarity_score"],
            scoring_method=raw["scoring_method"],
            matched_skills=[MatchedSkill(**s) for s in raw["matched_skills"]],
            not_found_skills=[NotFoundSkill(**s) for s in raw["not_found_skills"]],
            skill_coverage=raw["skill_coverage"],
            model_version=raw["model_version"],
            pipeline_version=raw["pipeline_version"],
            processed_at=datetime.now(timezone.utc),
            processing_time_ms=raw["processing_time_ms"],
            input_truncated=raw.get("input_truncated", False),
            note=raw.get("note"),
        )

        return SkillMatchingResponse(data=result)

    except RuntimeError as e:
        logger.error(f"Model error in skill matching: {e}")
        raise HTTPException(status_code=503, detail={
            "error": "model_unavailable",
            "message": str(e),
            "request_id": req.request_id,
        })
    except Exception as e:
        logger.exception(f"Unexpected error in skill matching: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "message": "Terjadi kesalahan internal saat memproses skill matching.",
            "request_id": req.request_id,
        })


@router.post("/skill-matching/batch", response_model=SkillMatchingBatchResponse)
async def skill_matching_batch(req: SkillMatchingBatchRequest):
    """
    Batch skill matching — proses beberapa pasang resume-lowongan sekaligus.
    Setiap item diproses independen; kegagalan satu item tidak menggagalkan yang lain.
    """
    if len(req.items) > settings.MAX_BATCH_SIZE:
        raise HTTPException(status_code=422, detail={
            "error": "batch_too_large",
            "message": f"Maksimum {settings.MAX_BATCH_SIZE} item per batch.",
        })

    results: list[SkillMatchingResult] = []
    completed = 0
    failed = 0

    for item in req.items:
        try:
            raw = compute_skill_matching(
                resume_text=item.resume_text,
                job_description=item.job_description,
                candidate_skills=item.candidate_skills,
                required_skills=item.required_skills,
            )

            result = SkillMatchingResult(
                request_id=item.request_id,
                candidate_id=item.candidate_id,
                job_id=item.job_id,
                input_version=item.input_version,
                status=raw["status"],
                cosine_similarity=raw["cosine_similarity"],
                similarity_score=raw["similarity_score"],
                scoring_method=raw["scoring_method"],
                matched_skills=[MatchedSkill(**s) for s in raw["matched_skills"]],
                not_found_skills=[NotFoundSkill(**s) for s in raw["not_found_skills"]],
                skill_coverage=raw["skill_coverage"],
                model_version=raw["model_version"],
                pipeline_version=raw["pipeline_version"],
                processed_at=datetime.now(timezone.utc),
                processing_time_ms=raw["processing_time_ms"],
                input_truncated=raw.get("input_truncated", False),
                note=raw.get("note"),
            )
            results.append(result)
            completed += 1

        except Exception as e:
            logger.exception(f"Batch item failed: {item.request_id}")
            results.append(SkillMatchingResult(
                request_id=item.request_id,
                candidate_id=item.candidate_id,
                job_id=item.job_id,
                status="failed",
                note=str(e),
            ))
            failed += 1

    return SkillMatchingBatchResponse(
        data=results,
        total=len(req.items),
        completed=completed,
        failed=failed,
    )
