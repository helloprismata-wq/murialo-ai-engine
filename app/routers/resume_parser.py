import os
import shutil
import tempfile
import logging
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hasil_parsing import HasilParsing
from app.services.resume_parser_service import jalankan_pipeline_parsing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume-parser", tags=["Resume Parser"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".webp"}


@router.get("/")
def resume_parser_status():
    """Status endpoint untuk modul Resume Parser."""
    return {
        "module": "resume-parser",
        "status": "ready",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "description": "Ekstraksi nama, kontak, keahlian/skill, riwayat kerja, dan pendidikan dari file CV"
    }


@router.post("/parse", status_code=status.HTTP_200_OK)
async def parse_resume(
    file: UploadFile = File(..., description="File CV (PDF, DOCX, atau Gambar)"),
    cv_id: Optional[int] = Form(None, description="ID CV dari database Laravel (opsional)"),
    pelamar_id: Optional[int] = Form(None, description="ID Pelamar/User dari database Laravel (opsional)"),
    db: Session = Depends(get_db),
):
    """
    Endpoint utama untuk mem-parse file CV yang dikirim dari Laravel (murialo-web).

    Alur kerja:
    1. Validasi format file
    2. Simpan file sementara di server
    3. Jalankan pipeline ekstraksi: teks -> spaCy NER -> deteksi skill -> riwayat kerja & pendidikan
    4. Simpan hasil ekstraksi ke tabel `hasil_parsings` di MySQL
    5. Hapus file sementara
    6. Kembalikan respons JSON lengkap untuk dipakai Modul 2 & 3
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file '{file_ext}' tidak didukung. Format yang diizinkan: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Simpan file ke direktori sementara
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Jalankan service parsing
        hasil_dict = jalankan_pipeline_parsing(temp_file_path)

        # Simpan atau update ke tabel hasil_parsings di database MySQL
        hasil_record = None
        if cv_id is not None:
            hasil_record = db.query(HasilParsing).filter(HasilParsing.cv_id == cv_id).first()

        if hasil_record:
            # Update record yang sudah ada
            hasil_record.pelamar_id = pelamar_id if pelamar_id is not None else hasil_record.pelamar_id
            hasil_record.nama_file = file.filename
            hasil_record.nama_lengkap = hasil_dict.get("nama_lengkap") or hasil_record.nama_lengkap
            hasil_record.email = hasil_dict.get("email") or hasil_record.email
            hasil_record.nomor_telepon = hasil_dict.get("nomor_telepon") or hasil_record.nomor_telepon
            hasil_record.skill_terdeteksi = hasil_dict.get("skill_terdeteksi")
            hasil_record.riwayat_kerja = hasil_dict.get("riwayat_kerja")
            hasil_record.pendidikan = hasil_dict.get("pendidikan")
            hasil_record.teks_mentah = hasil_dict.get("teks_mentah")
        else:
            # Buat record baru
            hasil_record = HasilParsing(
                cv_id=cv_id,
                pelamar_id=pelamar_id,
                nama_file=file.filename,
                nama_lengkap=hasil_dict.get("nama_lengkap", ""),
                email=hasil_dict.get("email", ""),
                nomor_telepon=hasil_dict.get("nomor_telepon", ""),
                skill_terdeteksi=hasil_dict.get("skill_terdeteksi", ""),
                riwayat_kerja=hasil_dict.get("riwayat_kerja", ""),
                pendidikan=hasil_dict.get("pendidikan", ""),
                teks_mentah=hasil_dict.get("teks_mentah", ""),
            )
            db.add(hasil_record)

        db.commit()
        db.refresh(hasil_record)

        return {
            "status": "success",
            "message": "CV berhasil diparse dan disimpan ke database",
            "data": hasil_record.to_dict()
        }

    except ValueError as ve:
        logger.warning(f"Validasi parsing gagal: {ve}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.exception(f"Terjadi kesalahan saat parsing CV: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses file CV: {str(e)}"
        )
    finally:
        # Bersihkan file sementara
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Gagal menghapus file sementara '{temp_file_path}': {e}")


@router.get("/by-cv/{cv_id}")
def get_parsing_by_cv_id(cv_id: int, db: Session = Depends(get_db)):
    """
    Ambil hasil parsing berdasarkan `cv_id` dari Laravel.
    Endpoint ini digunakan oleh Modul 2 (Skill Matching) dan Modul 3 (Smart Grading).
    """
    hasil = db.query(HasilParsing).filter(HasilParsing.cv_id == cv_id).first()
    if not hasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hasil parsing untuk cv_id {cv_id} tidak ditemukan"
        )
    return {
        "status": "success",
        "data": hasil.to_dict()
    }


@router.get("/{parsing_id}")
def get_parsing_by_id(parsing_id: int, db: Session = Depends(get_db)):
    """Ambil hasil parsing berdasarkan primary key ID."""
    hasil = db.query(HasilParsing).filter(HasilParsing.id == parsing_id).first()
    if not hasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hasil parsing dengan id {parsing_id} tidak ditemukan"
        )
    return {
        "status": "success",
        "data": hasil.to_dict()
    }


@router.get("/list/all")
def get_all_parsings(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Ambil daftar riwayat hasil parsing CV (terbaru dulu)."""
    items = (
        db.query(HasilParsing)
        .order_by(HasilParsing.diparse_pada.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(HasilParsing).count()
    return {
        "status": "success",
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [item.to_dict() for item in items]
    }
