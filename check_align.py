import spacy
from spacy.training import offsets_to_biluo_tags
from resume.training.training_data import TRAIN_DATA

nlp = spacy.blank("id") if spacy.util.is_package("id_core_news_sm") else spacy.blank("en")

for text, annotations in TRAIN_DATA:
    doc = nlp.make_doc(text)
    tags = offsets_to_biluo_tags(doc, annotations["entities"])
    if "-" in tags:
        print(f"Alignment error in: {text[:30]}...")
        for i, tag in enumerate(tags):
            if tag == "-":
                print(f"  Misaligned token: {doc[i]}")
