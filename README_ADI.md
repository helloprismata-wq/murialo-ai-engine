# Dokumentasi Modul Skripsi: Skill Matching & Smart Grading
**Penulis**: Adi  
**Judul Skripsi**: *Implementasi S-BERT dan Cosine Similarity untuk Automated Skill Matching dan Smart Grading Test*  
**Platform**: Rekrutmen Murialo (Laravel 11 + FastAPI AI Engine)

---

## Daftar Isi
1. [Ringkasan & Lingkup Modul](#1-ringkasan--lingkup-modul)
2. [Dasar Teori & Metodologi](#2-dasar-teori--metodologi)
3. [Modul 1: Automated Skill Matching](#3-modul-1-automated-skill-matching)
4. [Modul 2: Smart Grading Test](#4-modul-2-smart-grading-test)
5. [Arsitektur Integrasi Sistem (Laravel ↔ FastAPI)](#5-arsitektur-integrasi-sistem-laravel--fastapi)
6. [Struktur File & Komponen Terkait](#6-struktur-file--komponen-terkait)
7. [Panduan Menjalankan & Pengujian Mandiri](#7-panduan-menjalankan--pengujian-mandiri)
8. [Dataset & Evaluasi Model](#8-dataset--evaluasi-model)

---

## 1. Ringkasan & Lingkup Modul

Modul ini bertanggung jawab atas dua kapabilitas kecerdasan buatan utama dalam platform rekrutmen Murialo:

1. **Automated Skill Matching**: Mencocokkan profil/CV kandidat dengan deskripsi lowongan pekerjaan berdasarkan kemiripan semantik teks (*semantic text similarity*) dan identifikasi keahlian spesifik (*exact & alias skill coverage*).
2. **Smart Grading Test**: Menilai jawaban esai singkat (*short-answer open questions*) kandidat pada tes seleksi secara otomatis dengan membandingkan kesesuaian semantik terhadap satu atau beberapa jawaban acuan (*multi-reference sample answers*) yang ditentukan HR.

---

## 2. Dasar Teori & Metodologi

### A. Mengapa Sentence-BERT (S-BERT)?
* Model transformer standar (seperti vanilla BERT) menggunakan mekanisme *cross-encoder*, yang memerlukan waktu komputasi sangat tinggi ($O(n^2)$) untuk membandingkan pasangan kalimat karena kedua kalimat harus diproses bersamaan melalui seluruh self-attention layer.
* **S-BERT (Reimers & Gurevych, 2019)** menggunakan arsitektur *Siamese / Triplet Network* untuk menurunkan representasi vektor embedding kalimat yang bermakna semantik ke dalam ruang vektor berdimensi tetap (384-dim).
* Dengan S-BERT, setiap dokumen hanya perlu di-encode **sekali**, kemudian kemiripan antar pasangan dokumen dapat dihitung dengan **Cosine Similarity** dalam hitungan milidetik.

### B. Formula Cosine Similarity
Untuk vektor embedding teks kandidat $\mathbf{u}$ dan vektor teks acuan/lowongan $\mathbf{v}$:

$$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|} = \frac{\sum_{i=1}^{n} u_i v_i}{\sqrt{\sum_{i=1}^{n} u_i^2} \sqrt{\sum_{i=1}^{n} v_i^2}}$$

### C. Normalisasi Skor Persentase
$$\text{Skor} = \max\left(0.0, \min\left(100.0, \text{Cosine Similarity} \times 100\right)\right)$$

### D. Model yang Digunakan
* **Base Architecture**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Mendukung bahasa Indonesia dan Inggris).
* **Direktori Model Fine-Tuned**: `models/sbert-murialo/`
* **Device**: CPU (dioptimalkan untuk server tanpa GPU) / CUDA.

---

## 3. Modul 1: Automated Skill Matching

### A. Alur Kerja (Workflow)
```
[Teks CV / Resume Kandidat]      [Deskripsi & Persyaratan Lowongan]
              │                                      │
              ▼                                      ▼
    Preprocessing Teks                     Preprocessing Teks
              │                                      │
              └───────────────┬──────────────────────┘
                              ▼
                 S-BERT Model Encoding
                              │
                              ▼
                   Cosine Similarity Score
                              │
     ┌────────────────────────┴────────────────────────┐
     ▼                                                 ▼
[Kategori Kesesuaian]                       [Skill Gap Analysis]
- Good Fit (≥ 70%)                          - Matched Skills (Exact/Alias)
- Potential Fit (40% - 69%)                 - Missing / Not Found Skills
- No Fit (< 40%)                            - Skill Coverage (%)
```

### B. Fitur Unggulan Normalisasi Skill
Regex konvensional `\b` sering gagal mendeteksi skill dengan simbol khusus seperti `C++`, `C#`, `.NET`, atau `Node.js`. Modul ini mengimplementasikan deteksi khusus pada [`app/services/skill_normalization.py`](file:///d:/project%20murialo%20web/murialo-ai-engine/app/services/skill_normalization.py) dengan pemetaan alias cerdas.

### C. Endpoint FastAPI
* **`POST /api/v1/skill-matching`**:
  * Input: `resume_text`, `job_description`, `required_skills`, `candidate_skills`
  * Output: `similarity_score`, `cosine_similarity`, `matched_skills`, `not_found_skills`, `skill_coverage`.

### D. Antarmuka Web & CV Sandbox (Laravel)
* Akses URL: **`http://127.0.0.1:8000/lowongan/{id}/matching`**
* Fitur:
  * Tabel perankingan pelamar masuk berdasarkan skor kecocokan S-BERT.
  * **🧪 Sandbox Pengujian Teks CV Langsung**: HR dapat menempelkan teks CV atau ringkasan portofolio bebas untuk diuji kecocokannya terhadap lowongan tanpa perlu menunggu modul resume parser selesai dibuat.

---

## 4. Modul 2: Smart Grading Test

### A. Alur Kerja (Workflow)
```
[Jawaban Esai Kandidat]       [Daftar Jawaban Acuan HR (1 - 10)]
            │                                  │
            ▼                                  ▼
      Normalisasi                        Normalisasi
            │                                  │
            └────────────────┬─────────────────┘
                             ▼
               S-BERT Batch Embedding
                             │
                             ▼
       Cosine Similarity vs Tiap Jawaban Acuan
                             │
                             ▼
              Pilih Similarity Tertinggi (Max)
                             │
                             ▼
           Hitung Nilai: clamp(Max Sim, 0, 1) * Max Skor
                             │
                             ▼
           Draf Nilai Disimpan ke Sistem Penilaian
             (Menunggu Verifikasi Akhir oleh HR)
```

### B. Aturan & Edge Cases
* **Jawaban Kosong**: Menghasilkan skor `0.0` (bukan error 500/exception).
* **Multi-Reference**: Memungkinkan HR memasukkan variasi sudut pandang jawaban benar; AI mengambil kemiripan terbaik.
* **Human-in-the-Loop**: AI hanya membuat **draf penilaian** otomatis. HR berhak mengubah nilai akhir, menambahkan catatan, dan mempublikasikan hasil.

### C. Endpoint FastAPI
* **`POST /api/v1/smart-grading`**: Penilaian satu jawaban.
* **`POST /api/v1/smart-grading/batch`**: Penilaian simultan seluruh butir soal dalam satu sesi tes kandidat.

### D. Antarmuka Web & Verifikasi HR (Laravel)
* Akses URL: **`http://127.0.0.1:8000/penilaian/{id}`**
* Fitur:
  * Banner status evaluasi S-BERT (Prediksi Skor, Model, Waktu Inferensi).
  * Tombol **⚡ Jalankan Ulang AI**: Pemicu evaluasi ulang langsung secara sinkron jika ada pembaruan pada jawaban acuan.
  * Tombol **Ubah Penilaian**: Form verifikasi rubrik manual untuk HR.

---

## 5. Arsitektur Integrasi Sistem (Laravel ↔ FastAPI)

```
┌─────────────────────────────────┐        HTTP (REST)       ┌─────────────────────────────────┐
│     Laravel (murialo-web)       │ ───────────────────────> │  FastAPI (murialo-ai-engine)    │
│         Port: 8000              │                          │           Port: 8001            │
├─────────────────────────────────┤                          ├─────────────────────────────────┤
│ • Controllers:                  │                          │ • Lifespan Startup:             │
│   - SkillMatchingController     │                          │   - Muat Model S-BERT ke RAM    │
│   - PenilaianController         │                          │ • Routers:                      │
│ • Services:                     │                          │   - /api/v1/skill-matching      │
│   - AiEngineService             │ <─────────────────────── │   - /api/v1/smart-grading       │
│   - TesKandidatService          │        JSON Response     │   - /api/v1/health              │
│ • Queue Jobs:                   │                          │ • Core & Services:              │
│   - ProcessSmartGrading         │                          │   - Model Registry (Singleton)  │
│   - ProcessSkillMatching        │                          │   - Cosine Similarity Engine    │
│ • DB: ai_processing_results     │                          │   - Skill Normalization         │
└─────────────────────────────────┘                          └─────────────────────────────────┘
```

---

## 6. Struktur File & Komponen Terkait

### A. Repositori AI Engine (`murialo-ai-engine`)
| Path File | Fungsi Utama |
|---|---|
| `main.py` | Entry point FastAPI, lifecycle startup/shutdown model, middleware tracking |
| `app/core/config.py` | Konfigurasi Pydantic (device, path model, batas input) |
| `app/core/model_registry.py` | Singleton loader SentenceTransformer dengan Semaphore |
| `app/core/security.py` | Proteksi dependency `X-API-Key` |
| `app/services/skill_matching_service.py` | Logika komputasi S-BERT untuk Skill Matching |
| `app/services/smart_grading_service.py` | Logika komputasi S-BERT untuk Smart Grading |
| `app/services/skill_normalization.py` | Kamus alias dan boundary matcher keahlian |
| `app/services/text_processing.py` | Sanitasi teks, Unicode NFC, dan pencegahan overflow |
| `app/routers/skill_matching.py` | Router endpoint `/api/v1/skill-matching` |
| `app/routers/smart_grading.py` | Router endpoint `/api/v1/smart-grading` |
| `app/routers/health.py` | Router status kesehatan server & kesiapan model |
| `models/sbert-murialo/` | Folder bobot model S-BERT yang sudah difinetune |
| `tests/` | Rangkaian automated test Pytest (9 skenario pengujian) |
| `docs/API_CONTRACT_ADI.md` | Dokumentasi spesifikasi kontrak JSON request/response |
| `docs/murialo_ai_postman_collection.json` | Postman collection siap pakai |

### B. Repositori Web (`murialo-web`)
| Path File | Fungsi Utama |
|---|---|
| `app/Services/AiEngineService.php` | HTTP Client penghubung Laravel ke endpoint FastAPI |
| `app/Jobs/ProcessSmartGrading.php` | Background job pemroses Smart Grading setelah tes selesai |
| `app/Jobs/ProcessSkillMatching.php` | Background job pemroses kecocokan CV pelamar |
| `app/Models/AiProcessingResult.php` | Model Eloquent pencatat riwayat, skor, dan audit inferensi AI |
| `database/migrations/2026_09_22_000008_create_ai_processing_results_table.php` | Skema tabel database `ai_processing_results` |
| `app/Http/Controllers/SkillMatchingController.php` | Controller dashboard kecocokan skill & sandbox form |
| `app/Http/Controllers/PenilaianController.php` | Controller tampilan hasil tes & aksi retry AI |
| `resources/views/lowongan/matching.blade.php` | Halaman antarmuka Skill Matching & CV Sandbox |
| `resources/views/penilaian/show.blade.php` | Halaman peninjauan hasil tes dengan indikator AI |
| `routes/web.php` | Definisi route web untuk modul penilaian & matching |

---

## 7. Panduan Menjalankan & Pengujian Mandiri

### Langkah 1: Jalankan AI Engine
Buka terminal di direktori `murialo-ai-engine`:
```powershell
cd "d:\project murialo web\murialo-ai-engine"
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8001 --reload
```
* **Swagger UI / OpenAPI Docs**: Buka browser di [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### Langkah 2: Jalankan Laravel Web
Buka terminal di direktori `murialo-web`:
```powershell
cd "d:\project murialo web\murialo-web"
php artisan serve
```
* **Aplikasi Web**: Buka browser di [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Kredensial Login Pengujian (HTTP Basic Auth)
* **Akun HRD** (untuk menguji fitur penilaian dan skill matching):
  * Email / Username: `hrd@murialo.test`
  * Password: `password`
* **Akun Kandidat** (untuk menguji pengerjaan tes):
  * Email / Username: `budi.kandidat@murialo.test`
  * Password: `password`

### URL Langsung untuk Pengujian:
1. **Skill Matching & CV Sandbox**:  
   👉 `http://127.0.0.1:8000/lowongan/1/matching`  
   *(Ketik teks pengalaman kerja pada kotak sandbox di sisi kanan, klik **⚡ Uji Kecocokan S-BERT Sekarang**)*
2. **Smart Grading & Verifikasi HR**:  
   👉 `http://127.0.0.1:8000/penilaian/1`  
   *(Lihat banner skor AI S-BERT dan klik **⚡ Jalankan Ulang AI**)*
3. **Pengerjaan Tes Kandidat**:  
   👉 `http://127.0.0.1:8000/tes-saya`

### Menjalankan Unit Test Otomatis
* **Uji AI Engine (Pytest)**:
  ```powershell
  cd "d:\project murialo web\murialo-ai-engine"
  .\venv\Scripts\pytest.exe tests/ -v
  ```
  *(Status: 9 passed)*

* **Uji Web & Smart Grading Lifecycle (PHPUnit)**:
  ```powershell
  cd "d:\project murialo web\murialo-web"
  php artisan test --filter=SmartGradingTest
  ```
  *(Status: 12 passed, 50 assertions)*

---

## 8. Dataset & Evaluasi Model

### A. Lokasi Dataset
* Data evaluasi & training tersimpan di `data/skill_matching/`:
  * `train.csv`
  * `validation.csv`

### B. Menjalankan Evaluasi Akurasi (MAE & RMSE)
Untuk menghasilkan angka metrik evaluasi skripsi (MAE, RMSE, dan Akurasi Label):
```powershell
cd "d:\project murialo web\murialo-ai-engine"
.\venv\Scripts\python.exe scripts/evaluate_model.py
```
Skrip ini akan membandingkan prediksi S-BERT terhadap data validasi dan menampilkan metrik siap pakai untuk laporan skripsi.
