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
# 3. COLLABORATIVE FILTERING (versi sederhana, data dummy)
# ---------------------------------------------------------

# Histori interaksi dummy: siapa pernah dilamar ke posisi apa, hasilnya gimana.
# Nanti diganti data asli begitu sistem rekrutmen sungguhan mulai jalan.
histori_interaksi_dummy = [
    {"kandidat_id": "K001", "lowongan_id": "L002", "hasil": "diterima"},
    {"kandidat_id": "K003", "lowongan_id": "L001", "hasil": "diterima"},
    {"kandidat_id": "K004", "lowongan_id": "L002", "hasil": "ditolak"},
    {"kandidat_id": "K002", "lowongan_id": "L001", "hasil": "ditolak"},
    {"kandidat_id": "K003", "lowongan_id": "L002", "hasil": "diterima"},
]

# Bobot per hasil - "diterima" dianggap sinyal positif kuat,
# "ditolak" sinyal negatif ringan (bukan didiskualifikasi total).
BOBOT_HASIL = {"diterima": 1.0, "ditolak": -0.3, "lolos_screening": 0.5}


def collaborative_score(kandidat_id, lowongan, semua_lowongan, histori):
    """
    Skor Collaborative Filtering sederhana:
    lihat performa kandidat di lowongan-lowongan LAIN yang skill-nya
    mirip dengan lowongan target, berdasarkan histori interaksi.

    Ini versi dasar (belum pakai matrix factorization / KNN beneran),
    cukup buat kerangka awal sebelum dikembangkan lebih lanjut.
    """
    skor = 0.0
    jumlah_histori = 0

    for h in histori:
        if h["kandidat_id"] != kandidat_id:
            continue

        lowongan_lain = next(
            (l for l in semua_lowongan if l["lowongan_id"] == h["lowongan_id"]), None
        )
        if not lowongan_lain:
            continue

        # Seberapa mirip lowongan yang pernah dilamar vs lowongan target,
        # dari sisi kualifikasi skill (pakai fungsi yang sama seperti content-based).
        vectorizer = CountVectorizer()
        vectors = vectorizer.fit_transform([
            skills_to_text(lowongan["kualifikasi_skill"]),
            skills_to_text(lowongan_lain["kualifikasi_skill"]),
        ])
        kemiripan_lowongan = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

        bobot = BOBOT_HASIL.get(h["hasil"], 0)
        skor += kemiripan_lowongan * bobot
        jumlah_histori += 1

    if jumlah_histori == 0:
        return 0.0  # belum ada histori sama sekali -> netral

    return round(skor / jumlah_histori, 3)


# ---------------------------------------------------------
# 4. GABUNGKAN CONTENT-BASED + COLLABORATIVE JADI SKOR AKHIR
# ---------------------------------------------------------

def recommend_candidates_gabungan(lowongan, daftar_kandidat, semua_lowongan, histori,
                                   bobot_content=0.6, bobot_collab=0.4, top_n=3):
    """
    Gabungkan skor Content-Based dan Collaborative jadi satu skor akhir.
    Bobot 60/40 itu titik awal - bisa dituning kalau sudah ada data asli.
    """
    hasil_content = recommend_candidates(lowongan, daftar_kandidat, top_n=len(daftar_kandidat))
    hasil_gabungan = []

    for r in hasil_content:
        skor_collab = collaborative_score(r["kandidat_id"], lowongan, semua_lowongan, histori)
        skor_akhir = (bobot_content * r["skor_content_based"]) + (bobot_collab * skor_collab)

        hasil_gabungan.append({
            "kandidat_id": r["kandidat_id"],
            "nama": r["nama"],
            "skor_content_based": r["skor_content_based"],
            "skor_collaborative": skor_collab,
            "skor_akhir": round(skor_akhir, 3),
        })

    hasil_terurut = sorted(hasil_gabungan, key=lambda x: x["skor_akhir"], reverse=True)
    return hasil_terurut[:top_n]


# ---------------------------------------------------------
# 5. COBA JALANKAN
# ---------------------------------------------------------

if __name__ == "__main__":
    print("############################################")
    print("# VERSI 1: CONTENT-BASED FILTERING SAJA")
    print("############################################")
    for lowongan in lowongan_dummy:
        print(f"\n=== Rekomendasi untuk: {lowongan['posisi']} ({lowongan['lowongan_id']}) ===")
        print(f"Kualifikasi: {', '.join(lowongan['kualifikasi_skill'])}\n")

        rekomendasi = recommend_candidates(lowongan, kandidat_dummy, top_n=3)

        for i, r in enumerate(rekomendasi, start=1):
            print(f"{i}. {r['nama']} ({r['kandidat_id']}) - skor: {r['skor_content_based']}")

    print("\n\n############################################")
    print("# VERSI 2: GABUNGAN CONTENT-BASED + COLLABORATIVE")
    print("############################################")
    for lowongan in lowongan_dummy:
        print(f"\n=== Rekomendasi untuk: {lowongan['posisi']} ({lowongan['lowongan_id']}) ===")
        print(f"Kualifikasi: {', '.join(lowongan['kualifikasi_skill'])}\n")

        rekomendasi = recommend_candidates_gabungan(
            lowongan, kandidat_dummy, lowongan_dummy, histori_interaksi_dummy, top_n=3
        )

        for i, r in enumerate(rekomendasi, start=1):
            print(
                f"{i}. {r['nama']} ({r['kandidat_id']}) - "
                f"skor akhir: {r['skor_akhir']} "
                f"(content: {r['skor_content_based']}, collab: {r['skor_collaborative']})"
            )