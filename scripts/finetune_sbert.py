# scripts/finetune_sbert.py
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample
from sentence_transformers.losses import CosineSimilarityLoss
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader

# ── Konfigurasi ────────────────────────────────────────────────
BASE_MODEL  = "paraphrase-multilingual-MiniLM-L12-v2"
OUTPUT_DIR  = "models/sbert-murialo"
TRAIN_PATH  = "data/skill_matching/train.csv"
VAL_PATH    = "data/skill_matching/validation.csv"
EPOCHS      = 4
BATCH_SIZE  = 16
WARMUP_RATE = 0.1
# ───────────────────────────────────────────────────────────────


def load_data(path, max_rows=None):
    df = pd.read_csv(path).dropna(
        subset=['resume_text', 'job_description', 'ats_score']
    )
    if max_rows:
        df = df.head(max_rows)
    return df


def build_examples(df):
    examples = []
    for _, row in df.iterrows():
        label = float(row['ats_score']) / 100.0
        examples.append(InputExample(
            texts=[str(row['resume_text']), str(row['job_description'])],
            label=label
        ))
    return examples


def build_evaluator(val_df):
    sentences1, sentences2, scores = [], [], []
    for _, row in val_df.iterrows():
        sentences1.append(str(row['resume_text']))
        sentences2.append(str(row['job_description']))
        scores.append(float(row['ats_score']) / 100.0)

    return EmbeddingSimilarityEvaluator(
        sentences1, sentences2, scores,
        name='ats-val',
        write_csv=True,
    )


def print_summary(df_train, df_val, examples):
    print("=" * 55)
    print("  Fine-tuning SBERT — Prismata AI Engine")
    print("=" * 55)
    print(f"\n  Model dasar   : {BASE_MODEL}")
    print(f"  Output        : {OUTPUT_DIR}")
    print(f"  Data training : {len(df_train)} baris → {len(examples)} pasang")
    print(f"  Data validasi : {len(df_val)} baris")
    print(f"  Epochs        : {EPOCHS}")
    print(f"  Batch size    : {BATCH_SIZE}")

    ats = df_train['ats_score']
    print(f"\n  Distribusi ATS score (train):")
    print(f"    No Fit       (<40)  : {(ats < 40).sum()} baris")
    print(f"    Potential Fit(40-70): {((ats >= 40) & (ats < 70)).sum()} baris")
    print(f"    Good Fit     (>=70) : {(ats >= 70).sum()} baris")
    print()


def main():
    print("\nMemuat dataset...")
    df_train = load_data(TRAIN_PATH)
    df_val   = load_data(VAL_PATH)

    train_examples = build_examples(df_train)
    evaluator      = build_evaluator(df_val)

    print_summary(df_train, df_val, train_examples)

    print("  Memuat model dasar...")
    model = SentenceTransformer(BASE_MODEL)

    dataloader   = DataLoader(
        train_examples, shuffle=True, batch_size=BATCH_SIZE
    )
    loss_fn      = CosineSimilarityLoss(model)
    total_steps  = len(dataloader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATE)

    print(f"  Total steps   : {total_steps}")
    print(f"  Warmup steps  : {warmup_steps}")
    print(f"\n  Mulai training... (estimasi 45–90 menit di CPU)\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start = time.time()

    model.fit(
        train_objectives  = [(dataloader, loss_fn)],
        evaluator         = evaluator,
        epochs            = EPOCHS,
        warmup_steps      = warmup_steps,
        output_path       = OUTPUT_DIR,
        save_best_model   = True,
        show_progress_bar = True,
        evaluation_steps  = len(dataloader),
    )

    elapsed = time.time() - start
    print(f"\n  ✅ Fine-tuning selesai dalam {elapsed/60:.1f} menit!")
    print(f"  Model disimpan ke: {OUTPUT_DIR}")
    print(f"""
  Langkah selanjutnya:
  ─────────────────────────────────────────────────
  1. Buka  matching/ml_model.py
  2. Ganti MODEL_NAME:
     MODEL_NAME = "{OUTPUT_DIR}"

  3. Jalankan evaluasi ulang:
     python scripts/evaluate_model.py
  ─────────────────────────────────────────────────
    """)


if __name__ == '__main__':
    main()