# app/routers/smart_grading.py
"""
Router untuk endpoint Smart Grading.
Semua endpoint memerlukan API key (jika dikonfigurasi).
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import verify_api_key
from app.core.config import settings
from app.schemas.smart_grading import (
    SmartGradingRequest,
    SmartGradingBatchRequest,
    SmartGradingResponse,
    SmartGradingBatchResponse,
    SmartGradingResult,
)
from app.services.smart_grading_service import compute_smart_grading

logger = logging.getLogger("murialo.router.smart_grading")

router = APIRouter(
    prefix="/api/v1",
    tags=["Smart Grading"],
    dependencies=[Depends(verify_api_key)],
)


def _raw_to_result(raw: dict, req: SmartGradingRequest) -> SmartGradingResult:
    """Konversi output service ke schema response."""
    return SmartGradingResult(
        request_id=req.request_id,
        candidate_id=req.candidate_id,
        attempt_id=req.attempt_id,
        answer_id=req.answer_id,
        question_id=req.question_id,
        question_version=req.question_version,
        status=raw["status"],
        cosine_similarity=raw.get("cosine_similarity"),
        max_reference_similarity=raw.get("max_reference_similarity"),
        baseline_score=raw.get("baseline_score"),
        predicted_score=raw.get("predicted_score"),
        max_score=raw.get("max_score", req.max_score),
        scoring_method=raw["scoring_method"],
        is_calibrated=raw.get("is_calibrated", False),
        reason=raw.get("reason"),
        error_code=raw.get("error_code"),
        error_message=raw.get("error_message"),
        model_version=raw["model_version"],
        pipeline_version=raw["pipeline_version"],
        processed_at=datetime.now(timezone.utc),
        processing_time_ms=raw["processing_time_ms"],
    )


@router.post("/smart-grading", response_model=SmartGradingResponse)
async def smart_grading(req: SmartGradingRequest):
    """
    Penilaian semantik satu jawaban esai kandidat.

    Jawaban acuan dan max_score dikirim oleh backend Laravel dari snapshot tes,
    BUKAN dari request kandidat.
    """
    try:
        raw = compute_smart_grading(
            candidate_answer=req.candidate_answer,
            reference_answers=req.reference_answers,
            max_score=req.max_score,
        )

        # Jika service mengembalikan status failed (bukan error 5xx),
        # kembalikan sebagai response 200 dengan status failed
        result = _raw_to_result(raw, req)
        return SmartGradingResponse(data=result)

    except RuntimeError as e:
        logger.error(f"Model error in smart grading: {e}")
        raise HTTPException(status_code=503, detail={
            "error": "model_unavailable",
            "message": str(e),
            "request_id": req.request_id,
        })
    except Exception as e:
        logger.exception(f"Unexpected error in smart grading: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "message": "Terjadi kesalahan internal saat memproses smart grading.",
            "request_id": req.request_id,
        })


@router.post("/smart-grading/batch", response_model=SmartGradingBatchResponse)
async def smart_grading_batch(req: SmartGradingBatchRequest):
    """
    Batch smart grading — proses beberapa jawaban sekaligus.
    Setiap item diproses independen; kegagalan satu item tidak menggagalkan yang lain.
    """
    if len(req.items) > settings.MAX_BATCH_SIZE:
        raise HTTPException(status_code=422, detail={
            "error": "batch_too_large",
            "message": f"Maksimum {settings.MAX_BATCH_SIZE} item per batch.",
        })

    results: list[SmartGradingResult] = []
    completed = 0
    failed = 0

    for item in req.items:
        try:
            raw = compute_smart_grading(
                candidate_answer=item.candidate_answer,
                reference_answers=item.reference_answers,
                max_score=item.max_score,
            )
            result = _raw_to_result(raw, item)
            results.append(result)
            if result.status == "completed":
                completed += 1
            else:
                failed += 1

        except Exception as e:
            logger.exception(f"Batch item failed: {item.request_id}")
            results.append(SmartGradingResult(
                request_id=item.request_id,
                candidate_id=item.candidate_id,
                answer_id=item.answer_id,
                question_id=item.question_id,
                status="failed",
                error_code="processing_error",
                error_message=str(e),
                model_version="",
                pipeline_version="",
                processing_time_ms=0,
            ))
            failed += 1

    return SmartGradingBatchResponse(
        data=results,
        total=len(req.items),
        completed=completed,
        failed=failed,
    )
