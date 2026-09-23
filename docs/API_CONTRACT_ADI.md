# Kontrak API & Spesifikasi Modul — Adi
**Judul Skripsi**: *Implementasi S-BERT dan Cosine Similarity untuk Automated Skill Matching dan Smart Grading Test*  
**Platform**: Murialo Recruitment Engine

---

## 1. Arsitektur & Model
- **Base Model**: `paraphrase-multilingual-MiniLM-L12-v2` (Fine-tuned: `models/sbert-murialo`)
- **Framework**: FastAPI (Asynchronous, Type-safe with Pydantic v2)
- **Metrik Utama**:
  - Cosine Similarity:
    $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
  - Skor Normalisasi (0 - 100):
    $$\text{Skor} = \max\left(0, \min\left(100, \text{Cosine Similarity} \times 100\right)\right)$$

---

## 2. Endpoint Modul 1: Automated Skill Matching

### `POST /api/v1/skill-matching`
Mencocokkan teks resume kandidat dengan deskripsi lowongan pekerjaan.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <token>` (opsional di local dev)

**Request Body:**
```json
{
  "request_id": "optional-uuid",
  "candidate_id": "cand-123",
  "job_id": "job-456",
  "resume_text": "Pengalaman 3 tahun sebagai Full Stack Web Developer dengan Laravel, PHP, REST API, MySQL, dan Vue.js.",
  "job_description": "Dibutuhkan Backend Engineer yang menguasai Laravel, PHP, Database MySQL, dan arsitektur API.",
  "required_skills": ["Laravel", "PHP", "MySQL", "Docker"],
  "candidate_skills": ["Laravel", "PHP", "MySQL", "Vue.js"]
}
```

**Response Body (200 OK):**
```json
{
  "data": {
    "request_id": "uuid",
    "candidate_id": "cand-123",
    "job_id": "job-456",
    "status": "completed",
    "cosine_similarity": 0.8245,
    "similarity_score": 82.45,
    "scoring_method": "cosine_sbert",
    "matched_skills": [
      { "skill": "Laravel", "match_method": "exact" },
      { "skill": "PHP", "match_method": "exact" },
      { "skill": "MySQL", "match_method": "exact" }
    ],
    "not_found_skills": [
      { "skill": "Docker", "note": "Tidak ditemukan secara eksplisit di input." }
    ],
    "skill_coverage": 75.0,
    "model_version": "models/sbert-murialo",
    "pipeline_version": "1.0.0",
    "processing_time_ms": 48
  }
}
```

---

## 3. Endpoint Modul 2: Smart Grading Test

### `POST /api/v1/smart-grading`
Menilai kesesuaian semantik jawaban esai kandidat terhadap sekumpulan jawaban acuan.

**Request Body:**
```json
{
  "candidate_id": "cand-001",
  "question_id": "soal-10",
  "candidate_answer": "Dependency injection adalah pola desain di mana suatu objek disuplai dependensinya dari luar kelas.",
  "reference_answers": [
    "Dependency injection merupakan teknik pemisahan dependensi objek yang disuntikkan dari pihak luar."
  ],
  "max_score": 10.0
}
```

**Response Body (200 OK):**
```json
{
  "data": {
    "status": "completed",
    "cosine_similarity": 0.892,
    "baseline_score": 8.92,
    "predicted_score": 8.92,
    "max_score": 10.0,
    "scoring_method": "cosine_sbert_multi_ref",
    "model_version": "models/sbert-murialo",
    "pipeline_version": "1.0.0",
    "processing_time_ms": 32
  }
}
```

### `POST /api/v1/smart-grading/batch`
Menilai seluruh jawaban dalam satu sesi tes secara simultan.

---

## 4. Integrasi dengan Rekan Tim
- **Modul Danul (Resume Parser)**: Endpoint router `/resume-parser/parse` dipertahankan; integrasi otomatis dilakukan saat teks CV hasil parsing diteruskan ke `ProcessSkillMatching`.
- **Modul Raka (Rekomendasi Kandidat)**: Kontrak interface didefinisikan pada `app/contracts/raka_contract.py`.
- **Modul Habib (Dashboard Analitik)**: Kontrak interface didefinisikan pada `app/contracts/habib_contract.py`.
