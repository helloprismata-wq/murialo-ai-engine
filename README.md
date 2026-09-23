# Murialo AI Engine

AI Engine terpadu berbasis **FastAPI** untuk platform rekrutmen cerdas **Murialo**.

## Modul & Kontributor
1. **Adi**: Automated Skill Matching & Smart Grading Test menggunakan S-BERT dan Cosine Similarity (`app/routers/skill_matching.py`, `app/routers/smart_grading.py`).
2. **Danul**: Resume Parsing PDF/DOCX ke teks terstruktur (`app/routers/resume_parser.py`).
3. **Raka**: Rekomendasi Kandidat menggunakan Collaborative Filtering & Content-Based Filtering (`app/contracts/raka_contract.py`).
4. **Habib**: Dashboard Analitik menggunakan Time Series Forecasting, K-Means, dan NLG (`app/contracts/habib_contract.py`).

---

## Persyaratan Sistem
- Python 3.10+ (atau Python 3.11)
- PyTorch & Sentence-Transformers
- FastAPI & Uvicorn
- Model S-BERT: `models/sbert-murialo`

---

## Panduan Menjalankan

### 1. Buat & Aktifkan Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell
```

### 2. Instal Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan
Salin file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

### 4. Jalankan FastAPI Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
Akses dokumentasi interaktif Swagger UI di:
👉 `http://127.0.0.1:8001/docs`

---

## Pengujian Otomatis (Pytest)
Jalankan rangkaian test otomatis:
```bash
pytest tests/ -v
```

---

## Dokumentasi & Postman
- **Spesifikasi Kontrak API Adi**: [docs/API_CONTRACT_ADI.md](docs/API_CONTRACT_ADI.md)
- **Postman Collection**: [docs/murialo_ai_postman_collection.json](docs/murialo_ai_postman_collection.json)
