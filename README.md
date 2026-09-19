# murialo-ai-engine

AI Engine Murialo — modul kecerdasan buatan untuk rekrutmen (Python · FastAPI)

---

## Daftar Modul

| Modul | PIC | Status |
|---|---|---|
| Resume Parser | Khamdanul | 🔄 In Progress |
| **Rekomendasi Kandidat** | **Satyatma Raka Wiratama** | ⚠️ Data Dummy |
| Skill Matching | Adi | 🔄 In Progress |
| Users | — | ✅ Ready |

---

## Cara Menjalankan Server

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan server
uvicorn main:app --reload
```

Server berjalan di `http://localhost:8000`.
Dokumentasi interaktif tersedia di `http://localhost:8000/docs` (Swagger UI).

---

## Modul Rekomendasi Kandidat

> **File utama:**
> - Logic: [`app/services/recommendation.py`](app/services/recommendation.py)
> - Endpoint: [`app/routers/rekomendasi_kandidat.py`](app/routers/rekomendasi_kandidat.py)

### Cara Kerja (Algoritma)

Modul ini menggabungkan dua pendekatan:

1. **Content-Based Filtering** — menghitung kemiripan skill kandidat dengan kualifikasi lowongan menggunakan *cosine similarity* (CountVectorizer dari scikit-learn).
2. **Collaborative Filtering (sederhana)** — melihat histori performa kandidat di lowongan-lowongan lain yang skill-nya mirip dengan lowongan target.

Skor akhir dihitung dengan bobot gabungan:

```
skor_akhir = (0.6 × skor_content_based) + (0.4 × skor_collaborative)
```

Bobot 60/40 bisa dituning setelah data asli tersedia.

---

### Endpoint API

Base prefix: `/rekomendasi-kandidat`

#### `GET /rekomendasi-kandidat/`

Cek status modul.

**Response:**
```json
{
  "module": "rekomendasi-kandidat",
  "status": "ready"
}
```

---

#### `GET /rekomendasi-kandidat/{lowongan_id}?top_n=3`

Ambil daftar kandidat yang direkomendasikan untuk satu lowongan.

**Path Parameter:**

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `lowongan_id` | `string` | ID lowongan yang dicari rekomendasinya |

**Query Parameter:**

| Parameter | Tipe | Default | Deskripsi |
|---|---|---|---|
| `top_n` | `integer` | `3` | Jumlah kandidat teratas yang dikembalikan |

**Contoh Request:**
```
GET /rekomendasi-kandidat/L001?top_n=3
```

**Contoh Response `200 OK`:**
```json
{
  "lowongan_id": "L001",
  "posisi": "Backend Developer",
  "rekomendasi": [
    {
      "kandidat_id": "K003",
      "nama": "Kandidat C",
      "skor_content_based": 0.816,
      "skor_collaborative": 0.5,
      "skor_akhir": 0.69
    },
    {
      "kandidat_id": "K001",
      "nama": "Kandidat A",
      "skor_content_based": 0.333,
      "skor_collaborative": 0.0,
      "skor_akhir": 0.2
    },
    {
      "kandidat_id": "K004",
      "nama": "Kandidat D",
      "skor_content_based": 0.258,
      "skor_collaborative": 0.0,
      "skor_akhir": 0.155
    }
  ]
}
```

**Response `404 Not Found`** (lowongan tidak ditemukan):
```json
{
  "detail": "Lowongan L999 tidak ditemukan"
}
```

---

### Format Data yang Dibutuhkan dari Modul Lain

Begitu modul lain sudah jalan, sumber data dummy di `recommendation.py` perlu diganti dengan data asli. Berikut format yang diharapkan:

#### Data Kandidat *(dari modul Resume Parser — Khamdanul)*

```python
# List of dict
[
  {
    "kandidat_id": "K001",      # str  — ID unik kandidat
    "nama":        "Budi",      # str  — Nama lengkap
    "skills":      ["Python", "SQL", "Docker"]  # List[str] — daftar skill
  },
  ...
]
```

#### Data Lowongan *(dari database / modul job-listing)*

```python
# List of dict
[
  {
    "lowongan_id":       "L001",                         # str       — ID unik lowongan
    "posisi":            "Backend Developer",             # str       — Nama posisi
    "kualifikasi_skill": ["Python", "FastAPI", "SQL"]    # List[str] — skill yang dibutuhkan
  },
  ...
]
```

#### Data Histori Interaksi *(dari database rekrutmen)*

Digunakan oleh Collaborative Filtering untuk mempelajari pola penerimaan/penolakan kandidat.

```python
# List of dict
[
  {
    "kandidat_id": "K001",      # str — ID kandidat
    "lowongan_id": "L002",      # str — ID lowongan yang pernah dilamar
    "hasil":       "diterima"   # str — "diterima" | "ditolak" | "lolos_screening"
  },
  ...
]
```

Bobot per nilai `hasil` (sudah dikonfigurasi di `recommendation.py`):

| `hasil` | Bobot |
|---|---|
| `diterima` | `+1.0` |
| `lolos_screening` | `+0.5` |
| `ditolak` | `-0.3` |

---

### Status Saat Ini

> ⚠️ **Modul ini masih menggunakan data dummy.**
>
> Data kandidat, lowongan, dan histori interaksi saat ini di-*hardcode* langsung di [`app/services/recommendation.py`](app/services/recommendation.py) (variabel `kandidat_dummy`, `lowongan_dummy`, `histori_interaksi_dummy`) sebagai placeholder sampai modul lain siap diintegrasikan.

**Data dummy yang tersedia (untuk testing):**

| ID Lowongan | Posisi |
|---|---|
| `L001` | Backend Developer |
| `L002` | Data Analyst |

---

### Checklist — Yang Masih Perlu Dikerjakan

- [ ] **Integrasi data kandidat asli** — ganti `kandidat_dummy` dengan data dari modul Resume Parser (Khamdanul) setelah modul tersebut siap, pastikan format `skills` konsisten (list of string).
- [ ] **Integrasi data lowongan asli** — ganti `lowongan_dummy` dengan data dari database atau endpoint job-listing; pastikan field `kualifikasi_skill` tersedia.
- [ ] **Integrasi histori interaksi asli** — ganti `histori_interaksi_dummy` dengan data rekrutmen dari database (tabel lamaran / hasil screening).
- [ ] **Sinkronisasi format skill** — koordinasi dengan modul Skill Matching (Adi) supaya representasi skill konsisten (casing, singkatan, dll.) agar cosine similarity akurat.
- [ ] **Tuning bobot gabungan** — bobot `0.6 / 0.4` (content/collab) masih perkiraan awal; evaluasi ulang setelah data asli tersedia menggunakan metrik seperti Precision@K atau nDCG.
- [ ] **Upgrade Collaborative Filtering** — implementasi saat ini masih sederhana (item-based similarity). Pertimbangkan matrix factorization (SVD) atau pendekatan lain jika data histori sudah cukup banyak.
- [ ] **Tambah endpoint batch** — `POST /rekomendasi-kandidat/batch` untuk mengambil rekomendasi beberapa lowongan sekaligus dalam satu request.
- [ ] **Unit test** — tulis test case untuk `recommend_candidates()`, `collaborative_score()`, dan `recommend_candidates_gabungan()` dengan data yang terdefinisi.
- [ ] **Penanganan edge case** — kandidat tanpa skill, lowongan tanpa kualifikasi skill, atau corpus yang terlalu kecil untuk divektorisasi.

---

## Struktur Proyek

```
murialo-ai-engine/
├── main.py                          # Entry point FastAPI
├── requirements.txt
├── app/
│   ├── routers/
│   │   ├── rekomendasi_kandidat.py  # Endpoint modul rekomendasi
│   │   ├── resume_parser.py
│   │   └── users.py
│   └── services/
│       └── recommendation.py        # Logic Content-Based + Collaborative Filtering
```
