"""
resume/parser.py
================
MODUL 1 — Resume Parser dengan spaCy

Tugas modul ini:
1. Ekstrak teks mentah dari file CV (PDF atau DOCX)
2. Proses teks dengan spaCy NER untuk menemukan entitas
3. Deteksi skill dengan mencocokkan ke daftar skill yang diketahui
4. Simpan hasilnya ke database (tabel HasilParsing)

Alur:
  file CV (PDF/DOCX) --> ekstrak_teks() --> proses_spacy() --> HasilParsing (DB)
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# KAMUS SKILL — tambah sendiri sesuai kebutuhan proyek kalian
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
    """
    Ekstrak semua teks dari file PDF menggunakan pdfplumber.
    
    Args:
        path_file: Path absolut ke file PDF
    
    Returns:
        String teks mentah dari PDF
    """
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
    """
    Ekstrak semua teks dari file DOCX menggunakan python-docx.
    
    Args:
        path_file: Path absolut ke file DOCX
    
    Returns:
        String teks mentah dari DOCX
    """
    try:
        from docx import Document
        doc = Document(path_file)
        paragraf_list = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraf_list.append(para.text.strip())
        # Juga baca teks dari tabel (kalau CV-nya pakai format tabel)
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
    Ekstrak teks dari file gambar (foto CV) menggunakan OCR pytesseract.

    Cara kerja:
    1. Buka gambar dengan Pillow
    2. Pre-process: konversi ke grayscale, tingkatkan kontras
    3. Jalankan pytesseract OCR dengan bahasa Indonesia + Inggris

    Syarat instalasi:
        pip install pytesseract Pillow
        Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
        (Windows) Tambahkan path Tesseract ke settings.py jika perlu

    Args:
        path_file: Path absolut ke file gambar

    Returns:
        Teks hasil OCR
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        raise ImportError(
            "pytesseract atau Pillow belum diinstall.\n"
            "Jalankan: pip install pytesseract Pillow\n"
            "Lalu install Tesseract OCR dari: "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        )

    logger.info(f"  [OCR] Memproses gambar: {path_file}")

    # Buka dan pre-process gambar untuk hasil OCR lebih baik
    img = Image.open(path_file)

    # Konversi ke RGB jika perlu (menangani PNG transparan, WEBP, dll)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Konversi ke grayscale — OCR bekerja lebih baik di grayscale
    img_gray = img.convert("L")

    # Tingkatkan ketajaman (sharpness) untuk teks yang blur
    img_sharp = ImageEnhance.Sharpness(img_gray).enhance(2.0)

    # Tingkatkan kontras agar teks lebih jelas
    img_contrast = ImageEnhance.Contrast(img_sharp).enhance(1.5)

    # Jalankan OCR — coba Indonesia dulu, fallback ke Inggris
    try:
        # Coba pakai bahasa Indonesia + Inggris sekaligus
        teks = pytesseract.image_to_string(
            img_contrast,
            lang="ind+eng",
            config="--psm 6",  # psm 6 = anggap teks satu blok seragam
        )
        logger.info(f"  [OCR] Berhasil (ind+eng). Panjang teks: {len(teks)} karakter")
    except pytesseract.TesseractError:
        # Fallback: hanya bahasa Inggris (kalau bahasa Indonesia tidak terinstall)
        logger.warning("  [OCR] Model 'ind' tidak ada, fallback ke 'eng'")
        teks = pytesseract.image_to_string(
            img_contrast,
            lang="eng",
            config="--psm 6",
        )
        logger.info(f"  [OCR] Berhasil (eng). Panjang teks: {len(teks)} karakter")

    return teks


def ekstrak_teks(path_file: str) -> str:
    """
    Deteksi format file dan ekstrak teks secara otomatis.

    Format yang didukung:
      • PDF        → pdfplumber
      • DOCX/DOC   → python-docx
      • Gambar     → pytesseract OCR (JPG, PNG, WEBP, BMP, TIFF)

    Args:
        path_file: Path absolut ke file CV

    Returns:
        Teks mentah dari CV

    Raises:
        ValueError: Jika format file tidak didukung
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
    Cari nomor telepon Indonesia di dalam teks menggunakan regex.
    Mengenali format: 08xx, +628xx, 628xx (termasuk yang menggunakan spasi/strip/kurung)
    """
    pola = r"(?:\+62|62|0)[0-9 \-\(\)]{9,18}"
    hasil = re.search(pola, teks)
    if hasil:
        # Bersihkan karakter selain angka dan +
        bersih = re.sub(r"[^\d\+]", "", hasil.group(0))
        if len(bersih) >= 10:
            return bersih
    return ""


# ─────────────────────────────────────────────────────────────
# BAGIAN 3 — Deteksi Skill dari Teks
# ─────────────────────────────────────────────────────────────

def deteksi_skill(teks: str) -> list[str]:
    """
    Temukan skill di dalam teks CV dengan mencocokkan ke DAFTAR_SKILL.
    
    Cara kerja:
    - Ubah teks ke huruf kecil
    - Cek apakah setiap skill di kamus ada dalam teks
    - Menangani skill multi-kata (mis. "machine learning")
    
    Args:
        teks: Teks mentah dari CV
    
    Returns:
        List skill yang terdeteksi (sudah unik, diurutkan)
    """
    teks_lower = teks.lower()
    skill_ditemukan = set()
    
    for skill in DAFTAR_SKILL:
        # Untuk pencocokan yang lebih tepat, pakai word boundary
        # tapi perlu hati-hati dengan karakter khusus seperti "c++"
        skill_escaped = re.escape(skill)
        pola = rf"\b{skill_escaped}\b"
        if re.search(pola, teks_lower):
            skill_ditemukan.add(skill)
    
    return sorted(list(skill_ditemukan))


# ─────────────────────────────────────────────────────────────
# BAGIAN 4 — Ekstrak Riwayat Kerja & Pendidikan (Heuristik)
# ─────────────────────────────────────────────────────────────

# Kata kunci penanda awal seksi Pengalaman Kerja
KATA_KUNCI_KERJA = [
    "pengalaman kerja", "riwayat kerja", "experience", "work experience",
    "employment history", "professional experience", "pekerjaan",
]

# Kata kunci penanda awal seksi Pendidikan
KATA_KUNCI_PENDIDIKAN = [
    "pendidikan", "riwayat pendidikan", "education", "educational background",
    "academic background", "latar belakang pendidikan",
]

# Kata kunci penanda AKHIR dari seksi (dipakai buat tahu kapan berhenti baca)
KATA_KUNCI_SEKSI_LAIN = [
    "skill", "keahlian", "keterampilan", "organisasi", "penghargaan",
    "sertifikat", "project", "portofolio", "referensi", "hobi",
    "volunteer", "award", "certification", "language", "bahasa",
]


def _cari_seksi(baris_list: list[str], kata_kunci_awal: list[str]) -> list[str]:
    """
    Helper: cari baris yang termasuk dalam seksi tertentu di CV.
    
    Strategi:
    1. Temukan baris yang mengandung kata kunci awal seksi
    2. Kumpulkan baris sesudahnya sampai ketemu seksi baru
    
    Args:
        baris_list: Daftar baris teks CV
        kata_kunci_awal: Kata kunci yang menandai awal seksi yang dicari
    
    Returns:
        List baris yang termasuk dalam seksi tersebut
    """
    dalam_seksi = False
    hasil_baris = []
    
    for baris in baris_list:
        baris_lower = baris.strip().lower()
        
        # Cek apakah ini baris judul seksi yang dicari
        if any(kw in baris_lower for kw in kata_kunci_awal):
            dalam_seksi = True
            continue  # Lewati baris judul itu sendiri
        
        if dalam_seksi:
            # Cek apakah kita sudah masuk ke seksi berikutnya
            if any(kw in baris_lower for kw in KATA_KUNCI_SEKSI_LAIN):
                # Pastikan ini baris pendek (kemungkinan judul seksi, bukan isi)
                if len(baris.strip()) < 50:
                    break
            
            if baris.strip():  # Abaikan baris kosong
                hasil_baris.append(baris.strip())
    
    return hasil_baris


def ekstrak_riwayat_kerja(teks: str) -> str:
    """
    Ekstrak bagian riwayat kerja dari teks CV menggunakan pendekatan heuristik.
    
    Returns:
        String multi-baris berisi riwayat kerja yang terdeteksi
    """
    baris_list = teks.split("\n")
    baris_kerja = _cari_seksi(baris_list, KATA_KUNCI_KERJA)
    return "\n".join(baris_kerja[:30])  # Batasi 30 baris pertama


def ekstrak_pendidikan(teks: str) -> str:
    """
    Ekstrak bagian pendidikan dari teks CV menggunakan pendekatan heuristik.
    
    Returns:
        String multi-baris berisi data pendidikan yang terdeteksi
    """
    baris_list = teks.split("\n")
    baris_pendidikan = _cari_seksi(baris_list, KATA_KUNCI_PENDIDIKAN)
    return "\n".join(baris_pendidikan[:20])  # Batasi 20 baris pertama


# ─────────────────────────────────────────────────────────────
# BAGIAN 5 — Proses dengan spaCy NER
# ─────────────────────────────────────────────────────────────

def muat_model_spacy():
    """
    Muat model spaCy. Prioritaskan model hasil fine-tuning jika ada.
    
    Urutan prioritas:
    1. resume/models/resume_ner (Model fine-tuned khusus resume)
    2. en_core_web_sm (Model dasar ringan)
    3. en_core_web_md (Model dasar lebih akurat)
    
    Jalankan download model dulu:
        python -m spacy download en_core_web_sm
    
    Returns:
        Model spaCy yang sudah dimuat
    """
    try:
        import spacy
    except ImportError:
        raise ImportError(
            "spaCy belum diinstall. Jalankan: pip install spacy\n"
            "Lalu download model: python -m spacy download en_core_web_sm"
        )
    
    # 1. Coba muat model fine-tuned dulu
    finetuned_path = Path("resume/models/resume_ner")
    if finetuned_path.exists():
        try:
            nlp = spacy.load(finetuned_path)
            logger.info(f"Model spaCy fine-tuned berhasil dimuat: {finetuned_path}")
            return nlp
        except OSError as e:
            logger.warning(f"Gagal memuat model fine-tuned di {finetuned_path}: {e}")
    
    # 2. Fallback ke model bawaan
    for nama_model in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
        try:
            nlp = spacy.load(nama_model)
            logger.info(f"Model spaCy berhasil dimuat: {nama_model}")
            return nlp
        except OSError:
            logger.warning(f"Model '{nama_model}' tidak ditemukan, mencoba model berikutnya...")
    
    raise OSError(
        "Tidak ada model spaCy yang terinstall. "
        "Jalankan: python -m spacy download en_core_web_sm"
    )


def proses_dengan_spacy(teks: str) -> dict:
    """
    Proses teks CV dengan spaCy NER untuk mengekstrak entitas penting.
    
    spaCy NER label yang kita gunakan:
    - PERSON : nama orang → dipakai untuk nama_lengkap
    - ORG    : nama organisasi/perusahaan → dipakai untuk riwayat_kerja
    - GPE    : nama kota/negara
    - DATE   : tanggal/tahun
    
    Args:
        teks: Teks mentah dari CV
    
    Returns:
        Dict berisi entitas yang diekstrak
    """
    nlp = muat_model_spacy()
    
    # spaCy punya batas 1 juta karakter per dokumen
    # Potong teks jika terlalu panjang
    teks_diproses = teks[:100_000] if len(teks) > 100_000 else teks
    
    doc = nlp(teks_diproses)
    
    # Kumpulkan semua entitas per label
    entitas = {}
    for ent in doc.ents:
        label = ent.label_
        teks_ent = ent.text.strip()
        if teks_ent:
            entitas.setdefault(label, []).append(teks_ent)
    
    # Ambil nama orang pertama yang terdeteksi sebagai nama CV
    nama_lengkap = ""
    if "PERSON" in entitas:
        nama_lengkap = entitas["PERSON"][0]
    else:
        # Jika model fine-tuned menghilangkan label PERSON, muat model dasar untuk mengekstrak nama (di 1000 huruf pertama)
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
            logger.warning(f"Gagal memuat model dasar untuk deteksi nama: {e}")
            
    # Fallback heuristik: Jika tidak ada PERSON yang terdeteksi, ambil baris pertama yang berisi teks pendek tanpa angka
    if not nama_lengkap:
        for baris in teks[:500].split("\n"):
            bersih = baris.strip()
            # Kriteria nama: 1-5 kata, tidak mengandung angka, bukan email/url
            if bersih and 1 <= len(bersih.split()) <= 5 and not re.search(r"[\d@:]", bersih):
                nama_lengkap = bersih
                entitas.setdefault("PERSON", []).append(nama_lengkap)
                break
    
    # Nama organisasi → bisa jadi perusahaan tempat kerja
    organisasi = entitas.get("ORG", [])
    if not organisasi and "COMPANY" in entitas:
        organisasi = entitas["COMPANY"]
    
    logger.info(f"spaCy NER selesai. Entitas ditemukan: {list(entitas.keys())}")
    logger.debug(f"  PERSON: {entitas.get('PERSON', [])[:3]}")
    logger.debug(f"  ORG: {organisasi[:5]}")
    
    return {
        "nama_lengkap": nama_lengkap,
        "organisasi_ditemukan": organisasi,
        "entitas_lengkap": entitas,
    }


# ─────────────────────────────────────────────────────────────
# BAGIAN 6 — Fungsi Utama: parse_cv()
# ─────────────────────────────────────────────────────────────

def parse_cv(cv_instance) -> "HasilParsing":
    """
    FUNGSI UTAMA MODUL 1.
    
    Menerima instance model CV dari database,
    menjalankan seluruh pipeline parsing, dan menyimpan hasilnya
    ke tabel HasilParsing.
    
    Pipeline:
        CV (file) --> ekstrak_teks() --> proses_dengan_spacy()
                  --> deteksi_skill() --> ekstrak_riwayat_kerja()
                  --> ekstrak_pendidikan() --> HasilParsing (database)
    
    Args:
        cv_instance: Instance model CV (dari resume.models.CV)
    
    Returns:
        Instance HasilParsing yang sudah disimpan ke database
    
    Raises:
        Exception: Jika parsing gagal (file tidak bisa dibaca, dll)
    """
    from .models import HasilParsing
    
    logger.info(f"=== Mulai parsing CV: {cv_instance} ===")
    
    # --- Langkah 1: Dapatkan path file di server ---
    path_file = cv_instance.file_cv.path
    logger.info(f"Path file: {path_file}")
    
    # --- Langkah 2: Ekstrak teks mentah ---
    logger.info("Langkah 1/5: Mengekstrak teks dari file...")
    teks_mentah = ekstrak_teks(path_file)
    if not teks_mentah.strip():
        raise ValueError(
            "Tidak ada teks yang berhasil diekstrak dari CV. "
            "Pastikan file tidak rusak atau terproteksi password."
        )
    logger.info(f"  → {len(teks_mentah)} karakter berhasil diekstrak")
    
    # --- Langkah 3: Proses spaCy NER ---
    logger.info("Langkah 2/5: Menjalankan spaCy NER...")
    hasil_spacy = proses_dengan_spacy(teks_mentah)
    
    # --- Langkah 4: Deteksi Email & Telepon (regex) ---
    logger.info("Langkah 3/5: Mendeteksi email dan telepon...")
    email = deteksi_email(teks_mentah)
    telepon = deteksi_telepon(teks_mentah)
    
    # --- Langkah 5: Deteksi Skill ---
    logger.info("Langkah 4/5: Mendeteksi skill...")
    skill_list = deteksi_skill(teks_mentah)
    logger.info(f"  → {len(skill_list)} skill ditemukan: {skill_list}")
    
    # --- Langkah 6: Ekstrak Riwayat Kerja & Pendidikan ---
    logger.info("Langkah 5/5: Mengekstrak riwayat kerja dan pendidikan...")
    riwayat_kerja = ekstrak_riwayat_kerja(teks_mentah)
    pendidikan = ekstrak_pendidikan(teks_mentah)
    
    # --- Simpan ke database ---
    logger.info("Menyimpan hasil parsing ke database...")
    hasil, dibuat_baru = HasilParsing.objects.update_or_create(
        cv=cv_instance,
        defaults={
            "nama_lengkap": hasil_spacy.get("nama_lengkap", ""),
            "email": email,
            "nomor_telepon": telepon,
            "skill_terdeteksi": ", ".join(skill_list),
            "riwayat_kerja": riwayat_kerja,
            "pendidikan": pendidikan,
            "teks_mentah": teks_mentah,
        },
    )
    
    # Tandai CV sebagai sudah diparse
    cv_instance.sudah_diparse = True
    cv_instance.save(update_fields=["sudah_diparse"])
    
    status = "baru dibuat" if dibuat_baru else "diperbarui"
    logger.info(f"=== Parsing selesai! HasilParsing {status} (ID: {hasil.pk}) ===")
    
    return hasil
