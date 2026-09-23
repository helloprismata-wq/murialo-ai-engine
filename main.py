# main.py
"""
Entry point Murialo AI Engine.

Modul:
  - Adi: Skill Matching & Smart Grading (S-BERT + Cosine Similarity)
  - Raka: Rekomendasi Kandidat (routers: users, resume_parser — via app/routers/)
  - Habib: Dashboard Analitik (TBD)

Jangan mengganti file ini secara keseluruhan. Tambahkan router baru
dengan mempertahankan komponen anggota lain.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Router tim (Raka / Danul) — PERTAHANKAN ─────────────────────
from app.routers import resume_parser, users

# ── Router Adi (Skill Matching & Smart Grading) ──────────────────
from app.routers import health, skill_matching, smart_grading

# ── Model lifecycle ──────────────────────────────────────────────
from app.core.model_registry import load_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("murialo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Muat semua model AI ke memori (sekali per proses).
    Shutdown: Bersihkan resource jika diperlukan.
    """
    logger.info("═" * 50)
    logger.info("  Murialo AI Engine — Starting up")
    logger.info("═" * 50)

    try:
        load_models()
        logger.info("Semua model berhasil dimuat.")
    except Exception as e:
        logger.error(f"GAGAL memuat model: {e}")
        logger.warning("Server tetap berjalan, tetapi endpoint AI akan error 503.")

    yield

    logger.info("Murialo AI Engine — Shutting down")


app = FastAPI(
    title="Murialo AI Engine",
    description=(
        "AI Engine untuk rekrutmen Murialo.\n\n"
        "- **Skill Matching**: S-BERT + Cosine Similarity untuk mencocokkan CV dengan lowongan.\n"
        "- **Smart Grading**: Penilaian semantik jawaban esai terhadap jawaban acuan.\n"
        "- **Resume Parser**: (Danul — TBD)\n"
        "- **Rekomendasi Kandidat**: (Raka — CF/CBF)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracking(request: Request, call_next):
    """Tambahkan request_id dan timing ke setiap request."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time-Ms"] = str(elapsed_ms)
    return response


# ── Include Routers ──────────────────────────────────────────────

# Health (tanpa auth)
app.include_router(health.router)

# Tim: Raka / Danul — pertahankan apa adanya
app.include_router(resume_parser.router)
app.include_router(users.router)

# Adi: Skill Matching & Smart Grading
app.include_router(skill_matching.router)
app.include_router(smart_grading.router)


# ── Root endpoint (backward compatible) ──────────────────────────

﻿from fastapi import FastAPI
from app.routers import resume_parser, users

app = FastAPI(
    title="Murialo AI Engine",
    description="AI Engine Murialo — modul kecerdasan buatan untuk rekrutmen",
    version="1.0.0"
)

app.include_router(resume_parser.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Murialo AI Engine is running"}


@app.get("/health")
def health_check_legacy():
    """Health check lama — dipertahankan untuk backward compatibility."""
@app.get("/health")
def health_check():
    return {"status": "ok"}
