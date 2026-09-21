"""
app/services/resume_parser_service.py
=====================================
Service layer Modul 1 — Resume Parser (FastAPI version)

Diadaptasi dari resume/parser.py (Django) → pure Python, tanpa Django ORM.
Bisa dipanggil dari router FastAPI maupun dari modul lain.

Pipeline:
    file CV (PDF/DOCX/Gambar) → ekstrak_teks() → proses_dengan_spacy()
                              → deteksi_skill() → ekstrak_riwayat_kerja()
                              → ekstrak_pendidikan()
                              → dict hasil (siap disimpan ke DB atau dikembalikan JSON)
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# KAMUS SKILL — tambah sendiri sesuai kebutuhan
# ─────────────────────────────────────────────────────────────
DAFTAR_SKILL = {
    # Pemrograman
    "python", "java", "javascript", "js", "typescript", "c++", "c#", "c",
    "kotlin", "swift", "go", "rust", "ruby", "php", "scala", "r", "matlab",
    "dart", "flutter",
    # Web
    "html", "css", "react", "reactjs", "angular", "vue", "vuejs", "next.js",
    "nextjs", "nuxt", "django", "flask", "fastapi", "laravel", "spring",
    "node.js", "nodejs", "express", "bootstrap", "tailwind",
    # Data & AI
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas",
    "numpy", "matplotlib", "seaborn", "spacy", "nltk", "huggingface",
    "transformers", "bert", "gpt",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "git", "github",
    "gitlab", "ci/cd", "linux", "bash", "ansible", "terraform",
    # Mobile & Lainnya
    "android", "ios", "react native", "unity", "figma", "photoshop",
    "illustrator", "excel", "tableau", "power bi", "rest api", "graphql",
    "microservices", "agile", "scrum",
}


# ─────────────────────────────────────────────────────────────
# BAGIAN 1 — Ekstrak Teks dari File CV
# ─────────────────────────────────────────────────────────────

def ekstrak_teks_pdf(path_file: str) -> str:
    """Ekstrak teks dari PDF menggunakan pdfplumber."""
    try:
        import pdfplumber
        teks_semua = []
        with pdfplumber.open(path_file) as pdf:
            for nomor_halaman, halaman in enumerate(pdf.pages, start=1):
                teks = halaman.extract_text()
                if teks:
                    teks_semua.append(teks)
                    logger.debug(f"  [PDF] Halaman {nomor_halaman}: {len(teks)} karakter")
        return "\n".join(teks_semua)
    except ImportError:
        logger.error("pdfplumber belum diinstall. Jalankan: pip install pdfplumber")
        raise
    except Exception as e:
        logger.error(f"Gagal baca PDF '{path_file}': {e}")
        raise


def ekstrak_teks_docx(path_file: str) -> str:
    """Ekstrak teks dari DOCX menggunakan python-docx."""
    try:
        from docx import Document
        doc = Document(path_file)
        paragraf_list = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraf_list.append(para.text.strip())
        # Baca juga teks dari tabel
        for tabel in doc.tables:
            for baris in tabel.rows:
                for sel in baris.cells:
                    if sel.text.strip():
                        paragraf_list.append(sel.text.strip())
        return "\n".join(paragraf_list)
    except ImportError:
        logger.error("python-docx belum diinstall. Jalankan: pip install python-docx")
        raise
    except Exception as e:
        logger.error(f"Gagal baca DOCX '{path_file}': {e}")
        raise


EKSTENSI_GAMBAR = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def ekstrak_teks_gambar(path_file: str) -> str:
    """
    Ekstrak teks dari file gambar menggunakan OCR pytesseract.
    Perlu Tesseract OCR terinstall di sistem.
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance
    except ImportError:
        raise ImportError(
            "pytesseract atau Pillow belum diinstall.\n"
            "Jalankan: pip install pytesseract Pillow\n"
            "Lalu install Tesseract OCR dari: "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        )

    logger.info(f"  [OCR] Memproses gambar: {path_file}")
    img = Image.open(path_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img_gray = img.convert("L")
    img_sharp = ImageEnhance.Sharpness(img_gray).enhance(2.0)
    img_contrast = ImageEnhance.Contrast(img_sharp).enhance(1.5)

    try:
        teks = pytesseract.image_to_string(img_contrast, lang="ind+eng", config="--psm 6")
        logger.info(f"  [OCR] Berhasil (ind+eng). Panjang teks: {len(teks)} karakter")
    except pytesseract.TesseractError:
        logger.warning("  [OCR] Model 'ind' tidak ada, fallback ke 'eng'")
        teks = pytesseract.image_to_string(img_contrast, lang="eng", config="--psm 6")
        logger.info(f"  [OCR] Berhasil (eng). Panjang teks: {len(teks)} karakter")

    return teks


def ekstrak_teks(path_file: str) -> str:
    """
    Deteksi format file secara otomatis dan ekstrak teks.

    Format yang didukung:
      • PDF        → pdfplumber
      • DOCX/DOC   → python-docx
      • Gambar     → pytesseract OCR (JPG, PNG, WEBP, BMP, TIFF)
    """
    ekstensi = Path(path_file).suffix.lower()
    logger.info(f"Mengekstrak teks dari: {path_file} (format: {ekstensi})")

    if ekstensi == ".pdf":
        return ekstrak_teks_pdf(path_file)
    elif ekstensi in (".docx", ".doc"):
        return ekstrak_teks_docx(path_file)
    elif ekstensi in EKSTENSI_GAMBAR:
        return ekstrak_teks_gambar(path_file)
    else:
        raise ValueError(
            f"Format file '{ekstensi}' tidak didukung. "
            "Gunakan PDF, DOCX, JPG, PNG, atau WEBP."
        )


# ─────────────────────────────────────────────────────────────
# BAGIAN 2 — Deteksi Regex (Email, Telepon)
# ─────────────────────────────────────────────────────────────

def deteksi_email(teks: str) -> str:
    """Cari alamat email di dalam teks menggunakan regex."""
    pola = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    hasil = re.search(pola, teks)
    return hasil.group(0) if hasil else ""


def deteksi_telepon(teks: str) -> str:
    """
    Cari nomor telepon Indonesia di dalam teks.
    Mengenali format: 08xx, +628xx, 628xx (termasuk spasi/strip/kurung).
    """
    pola = r"(?:\+62|62|0)[0-9 \-\(\)]{9,18}"
    hasil = re.search(pola, teks)
    if hasil:
        bersih = re.sub(r"[^\d\+]", "", hasil.group(0))
        if len(bersih) >= 10:
            return bersih
    return ""


# ─────────────────────────────────────────────────────────────
# BAGIAN 3 — Deteksi Skill
# ─────────────────────────────────────────────────────────────

def deteksi_skill(teks: str) -> list[str]:
    """
    Temukan skill di dalam teks CV dengan mencocokkan ke DAFTAR_SKILL.
    Menggunakan word boundary agar pencocokan lebih akurat.
    """
    teks_lower = teks.lower()
    skill_ditemukan = set()

    for skill in DAFTAR_SKILL:
        skill_escaped = re.escape(skill)
        pola = rf"\b{skill_escaped}\b"
        if re.search(pola, teks_lower):
            skill_ditemukan.add(skill)

    return sorted(list(skill_ditemukan))


# ─────────────────────────────────────────────────────────────
# BAGIAN 4 — Ekstrak Riwayat Kerja & Pendidikan (Heuristik)
# ─────────────────────────────────────────────────────────────

KATA_KUNCI_KERJA = [
    "pengalaman kerja", "riwayat kerja", "experience", "work experience",
    "employment history", "professional experience", "pekerjaan",
]

KATA_KUNCI_PENDIDIKAN = [
    "pendidikan", "riwayat pendidikan", "education", "educational background",
    "academic background", "latar belakang pendidikan",
]

KATA_KUNCI_SEKSI_LAIN = [
    "skill", "keahlian", "keterampilan", "organisasi", "penghargaan",
    "sertifikat", "project", "portofolio", "referensi", "hobi",
    "volunteer", "award", "certification", "language", "bahasa",
]


def _cari_seksi(baris_list: list[str], kata_kunci_awal: list[str]) -> list[str]:
    """Helper: kumpulkan baris yang termasuk dalam seksi tertentu di CV."""
    dalam_seksi = False
    hasil_baris = []

    for baris in baris_list:
        baris_lower = baris.strip().lower()

        if any(kw in baris_lower for kw in kata_kunci_awal):
            dalam_seksi = True
            continue

        if dalam_seksi:
            if any(kw in baris_lower for kw in KATA_KUNCI_SEKSI_LAIN):
                if len(baris.strip()) < 50:
                    break
            if baris.strip():
                hasil_baris.append(baris.strip())

    return hasil_baris


def ekstrak_riwayat_kerja(teks: str) -> str:
    """Ekstrak bagian riwayat kerja dari teks CV (heuristik)."""
    baris_list = teks.split("\n")
    baris_kerja = _cari_seksi(baris_list, KATA_KUNCI_KERJA)
    return "\n".join(baris_kerja[:30])


def ekstrak_pendidikan(teks: str) -> str:
    """Ekstrak bagian pendidikan dari teks CV (heuristik)."""
    baris_list = teks.split("\n")
    baris_pendidikan = _cari_seksi(baris_list, KATA_KUNCI_PENDIDIKAN)
    return "\n".join(baris_pendidikan[:20])


# ─────────────────────────────────────────────────────────────
# BAGIAN 5 — Proses dengan spaCy NER
# ─────────────────────────────────────────────────────────────

def muat_model_spacy():
    """
    Muat model spaCy. Prioritaskan model fine-tuned jika ada.

    Urutan prioritas:
    1. resume/models/resume_ner (fine-tuned)
    2. en_core_web_sm
    3. en_core_web_md / en_core_web_lg
    """
    try:
        import spacy
    except ImportError:
        raise ImportError(
            "spaCy belum diinstall. Jalankan: pip install spacy\n"
            "Lalu download model: python -m spacy download en_core_web_sm"
        )

    finetuned_path = Path("resume/models/resume_ner")
    if finetuned_path.exists():
        try:
            nlp = spacy.load(finetuned_path)
            logger.info(f"Model spaCy fine-tuned dimuat: {finetuned_path}")
            return nlp
        except OSError as e:
            logger.warning(f"Gagal muat model fine-tuned: {e}")

    for nama_model in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
        try:
            nlp = spacy.load(nama_model)
            logger.info(f"Model spaCy dimuat: {nama_model}")
            return nlp
        except OSError:
            logger.warning(f"Model '{nama_model}' tidak ditemukan, mencoba berikutnya...")

    raise OSError(
        "Tidak ada model spaCy yang terinstall. "
        "Jalankan: python -m spacy download en_core_web_sm"
    )


def proses_dengan_spacy(teks: str) -> dict:
    """
    Proses teks CV dengan spaCy NER untuk mengekstrak entitas penting.

    Label spaCy yang digunakan:
    - PERSON : nama orang
    - ORG    : nama organisasi/perusahaan
    - GPE    : kota/negara
    - DATE   : tanggal/tahun
    """
    nlp = muat_model_spacy()
    teks_diproses = teks[:100_000] if len(teks) > 100_000 else teks
    doc = nlp(teks_diproses)

    entitas = {}
    for ent in doc.ents:
        label = ent.label_
        teks_ent = ent.text.strip()
        if teks_ent:
            entitas.setdefault(label, []).append(teks_ent)

    # Ambil nama orang pertama
    nama_lengkap = ""
    if "PERSON" in entitas:
        nama_lengkap = entitas["PERSON"][0]
    else:
        # Fallback: coba model dasar untuk ekstrak nama di 1000 karakter pertama
        try:
            import spacy
            nlp_dasar = spacy.load("en_core_web_sm")
            doc_awal = nlp_dasar(teks[:1000])
            for ent in doc_awal.ents:
                if ent.label_ == "PERSON":
                    nama_lengkap = ent.text.strip()
                    entitas.setdefault("PERSON", []).append(nama_lengkap)
                    break
        except Exception as e:
            logger.warning(f"Fallback nama gagal: {e}")

    # Fallback heuristik: baris pertama yang berisi teks pendek tanpa angka
    if not nama_lengkap:
        for baris in teks[:500].split("\n"):
            bersih = baris.strip()
            if bersih and 1 <= len(bersih.split()) <= 5 and not re.search(r"[\d@:]", bersih):
                nama_lengkap = bersih
                entitas.setdefault("PERSON", []).append(nama_lengkap)
                break

    organisasi = entitas.get("ORG", []) or entitas.get("COMPANY", [])

    logger.info(f"spaCy NER selesai. Entitas: {list(entitas.keys())}")

    return {
        "nama_lengkap": nama_lengkap,
        "organisasi_ditemukan": organisasi,
        "entitas_lengkap": entitas,
    }


# ─────────────────────────────────────────────────────────────
# BAGIAN 6 — Fungsi Utama: jalankan_pipeline_parsing()
# ─────────────────────────────────────────────────────────────

def jalankan_pipeline_parsing(path_file: str) -> dict:
    """
    FUNGSI UTAMA SERVICE.

    Menerima path file CV, menjalankan seluruh pipeline parsing,
    dan mengembalikan dict hasil (siap disimpan ke DB atau dikembalikan JSON).

    Pipeline:
        CV (file) → ekstrak_teks() → proses_dengan_spacy()
                  → deteksi_email/telepon → deteksi_skill()
                  → ekstrak_riwayat_kerja/pendidikan
                  → dict hasil

    Args:
        path_file: Path absolut ke file CV

    Returns:
        Dict berisi semua informasi hasil parsing

    Raises:
        ValueError: Jika file kosong atau format tidak didukung
    """
    logger.info(f"=== Mulai pipeline parsing: {path_file} ===")

    # Langkah 1: Ekstrak teks mentah
    logger.info("Langkah 1/5: Ekstrak teks...")
    teks_mentah = ekstrak_teks(path_file)
    if not teks_mentah.strip():
        raise ValueError(
            "Tidak ada teks yang berhasil diekstrak dari CV. "
            "Pastikan file tidak rusak atau terproteksi password."
        )
    logger.info(f"  → {len(teks_mentah)} karakter diekstrak")

    # Langkah 2: spaCy NER
    logger.info("Langkah 2/5: spaCy NER...")
    hasil_spacy = proses_dengan_spacy(teks_mentah)

    # Langkah 3: Email & Telepon
    logger.info("Langkah 3/5: Deteksi email & telepon...")
    email = deteksi_email(teks_mentah)
    telepon = deteksi_telepon(teks_mentah)

    # Langkah 4: Skill
    logger.info("Langkah 4/5: Deteksi skill...")
    skill_list = deteksi_skill(teks_mentah)
    logger.info(f"  → {len(skill_list)} skill ditemukan: {skill_list}")

    # Langkah 5: Riwayat Kerja & Pendidikan
    logger.info("Langkah 5/5: Riwayat kerja & pendidikan...")
    riwayat_kerja = ekstrak_riwayat_kerja(teks_mentah)
    pendidikan = ekstrak_pendidikan(teks_mentah)

    hasil = {
        "nama_lengkap": hasil_spacy.get("nama_lengkap", ""),
        "email": email,
        "nomor_telepon": telepon,
        "skill_terdeteksi": ", ".join(skill_list),
        "skill_list": skill_list,  # Format list untuk kemudahan Modul 2 & 3
        "riwayat_kerja": riwayat_kerja,
        "pendidikan": pendidikan,
        "teks_mentah": teks_mentah,
        "jumlah_skill": len(skill_list),
    }

    logger.info("=== Pipeline parsing selesai ===")
    return hasil
