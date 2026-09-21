import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import resume_parser, users
from app.database import engine, Base
import app.models  # Pastikan semua model ter-registrasi di Base metadata

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat tabel jika belum ada
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabel database berhasil diverifikasi/dibuat.")
    except Exception as e:
        logger.warning(f"Gagal menghubungkan atau membuat tabel database: {e}")
    yield

app = FastAPI(
    title="Murialo AI Engine",
    description="AI Engine Murialo — modul kecerdasan buatan untuk rekrutmen",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(resume_parser.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {
        "message": "Murialo AI Engine is running",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
