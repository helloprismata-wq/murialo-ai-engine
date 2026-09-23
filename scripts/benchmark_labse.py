# scripts/benchmark_labse.py
"""
Skrip untuk menguji akurasi mentah (raw) dari model LaBSE 
sebelum dilakukan fine-tuning.
Jalankan: python scripts/benchmark_labse.py
"""
import os
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Setup Path Absolut yang aman
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'validation.csv')

def get_label(score):
    if score < 40.0:
        return 'No Fit'
    elif score < 70.0:
        return 'Potential Fit'
    else:
        return 'Good Fit'

def main():
    print("="*60)
    print("🔍 BENCHMARK MODEL MENTAH: sentence-transformers/LaBSE")
    print("="*60)
    
    # 1. Load Model
    print("Memuat model LaBSE ke RAM...")
    print("(Proses ini memakan waktu agak lama karena ukuran model ~1.8GB)")
    model = SentenceTransformer('sentence-transformers/LaBSE')
    
    # 2. Load Dataset
    if not os.path.exists(DATASET_PATH):
        print(f"\n❌ Error: File dataset tidak ditemukan di:\n{DATASET_PATH}")
        return
        
    # Mengambil 100 sampel pertama agar evaluasi berjalan cepat di lokal
    df = pd.read_csv(DATASET_PATH).dropna(subset=['resume_text', 'job_description', 'ats_score']).head(100)
    print(f"\nMenguji {len(df)} sampel dari dataset validasi...")

    true_scores, pred_scores = [], []
    true_labels, pred_labels = [], []

    # 3. Proses Evaluasi
    for i, row in df.iterrows():
        # Encode teks menjadi vektor (LaBSE menghasilkan 768 dimensi)
        embeddings = model.encode(
            [str(row['resume_text']), str(row['job_description'])], 
            convert_to_numpy=True
        )
        
        # Hitung kemiripan
        cosine_raw = float(cosine_similarity(embeddings[0].reshape(1, -1), embeddings[1].reshape(1, -1))[0][0])
        score = max(0.0, min(100.0, cosine_raw * 100.0))
        
        pred_scores.append(score)
        pred_labels.append(get_label(score))
        true_scores.append(float(row['ats_score']))
        true_labels.append(str(row['original_label']))
        
        if (i + 1) % 20 == 0:
            print(f"  Progres: {i + 1}/{len(df)} selesai...")

    # 4. Kalkulasi Metrik Akhir
    mae = mean_absolute_error(true_scores, pred_scores)
    rmse = np.sqrt(mean_squared_error(true_scores, pred_scores))
    acc = sum(p == t for p, t in zip(pred_labels, true_labels)) / len(true_labels) * 100

    # Tampilkan Hasil
    print("\n" + "="*60)
    print("HASIL EVALUASI MENTAH (RAW) LaBSE")
    print("="*60)
    print(f"MAE            : {mae:.2f}  (Makin rendah makin baik)")
    print(f"RMSE           : {rmse:.2f}  (Makin rendah makin baik)")
    print(f"Label Accuracy : {acc:.1f}%")
    print("="*60)
    
    print("\nPerhatikan angkanya: Jika LaBSE mentah sudah lebih baik dari")
    print("MiniLM mentah (Akurasi 37.0%), bayangkan jika di-finetune nanti! 🔥")

if __name__ == '__main__':
    main()