# app/services/skill_normalization.py
"""
Normalisasi dan alias skill untuk pencocokan yang lebih akurat.

Masalah: substring match standar gagal mencocokkan "C++" karena regex
word boundary \\b tidak mengenali karakter khusus. Modul ini menangani
alias, case-insensitive matching, dan skill bertanda baca.
"""

import re
from typing import Optional


# Alias skill — key: bentuk yang dicari (lowercase), value: daftar alias
# Ketika salah satu alias ditemukan di teks, skill dianggap cocok.
DEFAULT_SKILL_ALIASES: dict[str, list[str]] = {
    "c++":       ["c++", "cpp", "c plus plus"],
    "c#":        ["c#", "csharp", "c sharp"],
    ".net":      [".net", "dotnet", "dot net"],
    "node.js":   ["node.js", "nodejs", "node js"],
    "react.js":  ["react.js", "reactjs", "react"],
    "vue.js":    ["vue.js", "vuejs", "vue"],
    "next.js":   ["next.js", "nextjs"],
    "express.js": ["express.js", "expressjs", "express"],
    "asp.net":   ["asp.net", "aspnet"],
    "vb.net":    ["vb.net", "vbnet", "visual basic .net"],
    "objective-c": ["objective-c", "objectivec", "obj-c"],
    "f#":        ["f#", "fsharp"],
    "t-sql":     ["t-sql", "tsql", "transact-sql"],
    "pl/sql":    ["pl/sql", "plsql"],
}


def _build_pattern(term: str) -> re.Pattern:
    """
    Bangun regex pattern untuk mencocokkan skill term dalam teks.
    Menggunakan \\b jika term berisi huruf/angka di batas,
    atau lookaround untuk term dengan karakter khusus di batas.
    """
    escaped = re.escape(term)
    # Jika term dimulai/diakhiri dengan karakter non-word, \\b tidak tepat
    start_boundary = r'\b' if re.match(r'\w', term[0]) else r'(?<!\w)'
    end_boundary = r'\b' if re.match(r'\w', term[-1]) else r'(?!\w)'
    return re.compile(start_boundary + escaped + end_boundary, re.IGNORECASE)


def normalize_skill_name(skill: str) -> str:
    """Normalisasi nama skill untuk penyimpanan konsisten."""
    return skill.strip()


def match_skill_in_text(
    skill: str,
    text: str,
    aliases: Optional[dict[str, list[str]]] = None,
) -> tuple[bool, str]:
    """
    Cek apakah skill ditemukan dalam teks.

    Returns:
        (found, match_method) — match_method: 'exact' | 'alias' | 'not_found'
    """
    if aliases is None:
        aliases = DEFAULT_SKILL_ALIASES

    skill_lower = skill.lower().strip()
    text_lower = text.lower()

    # 1. Coba exact match
    pattern = _build_pattern(skill_lower)
    if pattern.search(text_lower):
        return True, "exact"

    # 2. Coba alias match
    alias_list = aliases.get(skill_lower, [])
    for alias in alias_list:
        alias_pattern = _build_pattern(alias.lower())
        if alias_pattern.search(text_lower):
            return True, "alias"

    return False, "not_found"
