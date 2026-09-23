# app/services/text_processing.py
"""
Utilitas preprocessing teks untuk pipeline AI.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalisasi teks input:
    - Unicode NFC normalization
    - Collapse whitespace berlebih
    - Strip leading/trailing whitespace
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_with_notice(text: str, max_length: int) -> tuple[str, bool]:
    """
    Potong teks jika melebihi max_length karakter.

    Returns:
        (text, was_truncated)
    """
    if len(text) <= max_length:
        return text, False
    return text[:max_length], True


def is_blank(text: str | None) -> bool:
    """Cek apakah teks kosong atau hanya whitespace."""
    return not text or not text.strip()
