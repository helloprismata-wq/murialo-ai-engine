"""
Content-Based Filtering - Modul Rekomendasi Kandidat
Murialo - Satyatma Raka Wiratama

Versi paling sederhana: cocokkan skill kandidat vs kualifikasi lowongan
pakai cosine similarity. Masih pakai data dummy, belum terhubung ke
modul lain (resume-parser / skill-matching).
"""

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------
# 1. DATA DUMMY - nanti diganti data asli dari modul lain
# ---------------------------------------------------------

kandidat_dummy = [
    {"kandidat_id": "K001", "nama": "Kandidat A", "skills": ["Python", "Machine Learning", "SQL"]},
    {"kandidat_id": "K002", "nama": "Kandidat B", "skills": ["Java", "React", "Spring Boot"]},
    {"kandidat_id": "K003", "nama": "Kandidat C", "skills": ["Python", "FastAPI", "SQL", "Docker"]},
    {"kandidat_id": "K004", "nama": "Kandidat D", "skills": ["Python", "Data Analysis", "Excel"]},
    {"kandidat_id": "K005", "nama": "Kandidat E", "skills": ["PHP", "Laravel", "MySQL"]},
]

lowongan_dummy = [
    {"lowongan_id": "L001", "posisi": "Backend Developer", "kualifikasi_skill": ["Python", "FastAPI", "SQL"]},
    {"lowongan_id": "L002", "posisi": "Data Analyst", "kualifikasi_skill": ["Python", "SQL", "Data Analysis"]},
]


# ---------------------------------------------------------
# 2. FUNGSI UTAMA: hitung kemiripan skill kandidat vs lowongan
# ---------------------------------------------------------

def skills_to_text(skills):
    """Ubah list skill jadi satu string, biar bisa divectorize."""
    return " ".join(skill.replace(" ", "_") for skill in skills)


def recommend_candidates(lowongan, daftar_kandidat, top_n=3):
    """
    Rekomendasikan kandidat paling cocok untuk satu lowongan,
    berdasarkan kemiripan skill (Content-Based Filtering).
    """
    # Gabungkan teks skill lowongan + semua kandidat jadi satu corpus
    lowongan_text = skills_to_text(lowongan["kualifikasi_skill"])
    kandidat_texts = [skills_to_text(k["skills"]) for k in daftar_kandidat]

    corpus = [lowongan_text] + kandidat_texts

    # Vectorize teks jadi angka (bag-of-words sederhana)
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(corpus)

    # Hitung cosine similarity: lowongan (baris 0) vs tiap kandidat
    lowongan_vector = vectors[0:1]
    kandidat_vectors = vectors[1:]
    skor_similarity = cosine_similarity(lowongan_vector, kandidat_vectors)[0]

    # Gabungkan skor dengan data kandidat
    hasil = []
    for kandidat, skor in zip(daftar_kandidat, skor_similarity):
        hasil.append({
            "kandidat_id": kandidat["kandidat_id"],
            "nama": kandidat["nama"],
            "skor_content_based": round(float(skor), 3),
        })

    # Urutkan dari skor tertinggi
    hasil_terurut = sorted(hasil, key=lambda x: x["skor_content_based"], reverse=True)

    return hasil_terurut[:top_n]


# ---------------------------------------------------------
# 3. COBA JALANKAN
# ---------------------------------------------------------

if __name__ == "__main__":
    for lowongan in lowongan_dummy:
        print(f"\n=== Rekomendasi untuk: {lowongan['posisi']} ({lowongan['lowongan_id']}) ===")
        print(f"Kualifikasi: {', '.join(lowongan['kualifikasi_skill'])}\n")

        rekomendasi = recommend_candidates(lowongan, kandidat_dummy, top_n=3)

        for i, r in enumerate(rekomendasi, start=1):
            print(f"{i}. {r['nama']} ({r['kandidat_id']}) - skor: {r['skor_content_based']}")