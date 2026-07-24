"""
core/numbers.py
Conversor de texto a números. Independiente de Flet.
"""
import re
import unicodedata
from typing import Optional

# Diccionarios escalables
LANG_DATA = {
    "es": {
        "connector": "y",
        "units": {"cero": 0, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9},
        "teens": {"diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19},
        "compounds": {"veinte": 20, "veintiuno": 21, "veintiuna": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29},
        "tens": {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90},
    },
    "en": {
        "connector": "and",
        "units": {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9},
        "teens": {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19},
        "compounds": {},
        "tens": {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90},
    }
}

def _normalize(text: str) -> str:
    if not text: return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn") # Quitar tildes
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()

def text_to_number(text: str, lang: str = "es") -> Optional[int]:
    """Convierte texto hablado a número entero. Ej: 'veintitrés' -> 23"""
    clean = _normalize(text)
    if not clean: return None
    
    # 1. Buscar dígitos directos primero
    digit_match = re.search(r'\b\d+\b', clean)
    if digit_match:
        return int(digit_match.group())

    tokens = clean.split(" ")
    data = LANG_DATA.get(lang, LANG_DATA["es"])
    results = []
    i = 0
    n = len(tokens)

    while i < n:
        token = tokens[i]
        if token in data.get("compounds", {}):
            results.append(data["compounds"][token])
            i += 1
        elif token in data["tens"]:
            tens_val = data["tens"][token]
            j = i + 1
            if j < n and tokens[j] == data["connector"]:
                j += 1
            if j < n and tokens[j] in data["units"]:
                results.append(tens_val + data["units"][tokens[j]])
                i = j + 1
            else:
                results.append(tens_val)
                i += 1
        elif token in data["teens"]:
            results.append(data["teens"][token])
            i += 1
        elif token in data["units"]:
            results.append(data["units"][token])
            i += 1
        else:
            i += 1
            
    return results[0] if results else None