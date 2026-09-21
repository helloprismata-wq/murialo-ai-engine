"""
resume/training/finetune.py
Script untuk melatih (fine-tune) model spaCy menggunakan data di training_data.py.
"""

import spacy
from spacy.training.example import Example
import random
import os
from pathlib import Path

from .training_data import TRAIN_DATA

def train_spacy(model_name="en_core_web_sm", output_dir="resume/models/resume_ner", iterations=20):
    """
    Melatih model NER spaCy dengan data tambahan.
    """
    print(f"Memuat model dasar: {model_name}")
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model {model_name} tidak ditemukan. Mendownload...")
        from spacy.cli import download
        download(model_name)
        nlp = spacy.load(model_name)

    # Dapatkan komponen NER
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Tambahkan label baru ke NER
    for _, annotations in TRAIN_DATA:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # Nonaktifkan komponen lain agar hanya NER yang dilatih
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    print("Mulai proses fine-tuning...")
    with nlp.disable_pipes(*unaffected_pipes):
        optimizer = nlp.resume_training()
        
        for itn in range(iterations):
            random.shuffle(TRAIN_DATA)
            losses = {}
            
            # Buat batch training
            for text, annotations in TRAIN_DATA:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                nlp.update(
                    [example],
                    drop=0.3,  # Dropout agar tidak overfitting
                    sgd=optimizer,
                    losses=losses,
                )
            print(f"Epoch {itn+1}/{iterations} - Loss: {losses}")

    # Simpan model
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    nlp.to_disk(output_path)
    print(f"Model berhasil disimpan ke: {output_path.absolute()}")

if __name__ == "__main__":
    train_spacy()
