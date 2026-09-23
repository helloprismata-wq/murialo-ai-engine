# scripts/analyze_score_distribution.py
"""
Analisis distribusi skor prediksi vs skor asli.
Jalankan dari D:\prismata: python scripts/analyze_score_distribution.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prismata.settings')
import django; django.setup()

import pandas as pd
import numpy as np
from matching.services import compute_compatibility

df = pd.read_csv('dataset/validation.csv').dropna().head(50)

pred_scores, true_scores, true_labels = [], [], []

print("Menganalisis 50 sampel...")
for _, row in df.iterrows():
    result = compute_compatibility(str(row['resume_text']), str(row['job_description']))
    pred_scores.append(result['score'])
    true_scores.append(float(row['ats_score']))
    true_labels.append(str(row['original_label']))

pred = np.array(pred_scores)
true = np.array(true_scores)

print(f"\n── Distribusi skor PREDIKSI kita ──────────────")
print(f"  Min    : {pred.min():.1f}")
print(f"  Max    : {pred.max():.1f}")
print(f"  Rata2  : {pred.mean():.1f}")
print(f"  Median : {np.median(pred):.1f}")

print(f"\n── Distribusi skor ASLI dataset ───────────────")
print(f"  Min    : {true.min():.1f}")
print(f"  Max    : {true.max():.1f}")
print(f"  Rata2  : {true.mean():.1f}")
print(f"  Median : {np.median(true):.1f}")

print(f"\n── Skor prediksi per label asli ───────────────")
for label in ['No Fit', 'Potential Fit', 'Good Fit']:
    idx = [i for i, l in enumerate(true_labels) if l == label]
    if idx:
        scores = pred[[i for i in idx]]
        print(f"  {label:<15}: prediksi rata2 = {scores.mean():.1f}  "
              f"(asli rata2 = {true[[i for i in idx]].mean():.1f})")