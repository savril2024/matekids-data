"""
core/number_parser.py
Parser de números en palabras para múltiples idiomas.
Soporta: español, inglés, francés, portugués, alemán, italiano.
"""
import re
from typing import Optional, Dict, List

# Diccionarios de números en palabras por idioma
NUMBER_WORDS = {
    "es": {
        0: "cero", 1: "uno", 2: "dos", 3: "tres", 4: "cuatro",
        5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve",
        10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
        15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho",
        19: "diecinueve", 20: "veinte", 21: "veintiuno", 22: "veintidós",
        23: "veintitrés", 24: "veinticuatro", 25: "veinticinco",
        26: "veintiséis", 27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
        30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
        70: "setenta", 80: "ochenta", 90: "noventa", 100: "cien"
    },
    "en": {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
        15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
        19: "nineteen", 20: "twenty", 21: "twenty-one", 22: "twenty-two",
        23: "twenty-three", 24: "twenty-four", 25: "twenty-five",
        26: "twenty-six", 27: "twenty-seven", 28: "twenty-eight",
        29: "twenty-nine", 30: "thirty", 40: "forty", 50: "fifty",
        60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety", 100: "one hundred"
    },
    "fr": {
        0: "zéro", 1: "un", 2: "deux", 3: "trois", 4: "quatre",
        5: "cinq", 6: "six", 7: "sept", 8: "huit", 9: "neuf",
        10: "dix", 11: "onze", 12: "douze", 13: "treize", 14: "quatorze",
        15: "quinze", 16: "seize", 17: "dix-sept", 18: "dix-huit",
        19: "dix-neuf", 20: "vingt", 21: "vingt et un", 22: "vingt-deux",
        23: "vingt-trois", 24: "vingt-quatre", 25: "vingt-cinq",
        30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante",
        70: "soixante-dix", 80: "quatre-vingts", 90: "quatre-vingt-dix",
        100: "cent"
    },
    "pt": {
        0: "zero", 1: "um", 2: "dois", 3: "três", 4: "quatro",
        5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove",
        10: "dez", 11: "onze", 12: "doze", 13: "treze", 14: "quatorze",
        15: "quinze", 16: "dezesseis", 17: "dezessete", 18: "dezoito",
        19: "dezenove", 20: "vinte", 21: "vinte e um", 22: "vinte e dois",
        23: "vinte e três", 24: "vinte e quatro", 25: "vinte e cinco",
        30: "trinta", 40: "quarenta", 50: "cinquenta", 60: "sessenta",
        70: "setenta", 80: "oitenta", 90: "noventa", 100: "cem"
    },
    "de": {
        0: "null", 1: "eins", 2: "zwei", 3: "drei", 4: "vier",
        5: "fünf", 6: "sechs", 7: "sieben", 8: "acht", 9: "neun",
        10: "zehn", 11: "elf", 12: "zwölf", 13: "dreizehn", 14: "vierzehn",
        15: "fünfzehn", 16: "sechzehn", 17: "siebzehn", 18: "achtzehn",
        19: "neunzehn", 20: "zwanzig", 21: "einundzwanzig", 22: "zweiundzwanzig",
        23: "dreiundzwanzig", 24: "vierundzwanzig", 25: "fünfundzwanzig",
        30: "dreißig", 40: "vierzig", 50: "fünfzig", 60: "sechzig",
        70: "siebzig", 80: "achtzig", 90: "neunzig", 100: "einhundert"
    },
    "it": {
        0: "zero", 1: "uno", 2: "due", 3: "tre", 4: "quattro",
        5: "cinque", 6: "sei", 7: "sette", 8: "otto", 9: "nove",
        10: "dieci", 11: "undici", 12: "dodici", 13: "tredici", 14: "quattordici",
        15: "quindici", 16: "sedici", 17: "diciassette", 18: "diciotto",
        19: "diciannove", 20: "venti", 21: "ventuno", 22: "ventidue",
        23: "ventitré", 24: "ventiquattro", 25: "venticinque",
        30: "trenta", 40: "quaranta", 50: "cinquanta", 60: "sessanta",
        70: "settanta", 80: "ottanta", 90: "novanta", 100: "cento"
    }
}

# Mapeo inverso: palabra -> número (para búsqueda rápida)
def build_reverse_map(lang: str) -> Dict[str, int]:
    """Construye un diccionario inverso: palabra -> número."""
    reverse = {}
    for num, word in NUMBER_WORDS.get(lang, {}).items():
        # Normalizar: minúsculas, sin tildes para búsqueda flexible
        clean_word = word.lower().strip()
        reverse[clean_word] = num
        # También agregar sin tildes
        no_accents = clean_word.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        if no_accents != clean_word:
            reverse[no_accents] = num
    return reverse

# Cache de mapas inversos
_reverse_maps = {}

def get_reverse_map(lang: str) -> Dict[str, int]:
    if lang not in _reverse_maps:
        _reverse_maps[lang] = build_reverse_map(lang)
    return _reverse_maps[lang]


def text_to_number(text: str, lang: str = "es") -> Optional[int]:
    """
    Convierte texto a número. Soporta:
    - Números directos: "5", "12"
    - Palabras en el idioma: "cinco", "five", "cinq"
    - Frases mixtas: "tengo cinco manzanas" -> 5
    - Números con texto alrededor: "son 5 peces" -> 5
    
    Args:
        text: Texto a parsear
        lang: Código de idioma ("es", "en", "fr", "pt", "de", "it")
    
    Returns:
        Número entero o None si no se encuentra
    """
    if not text:
        return None
    
    # 1. Intentar extraer número directo (ej: "5", "12")
    numbers = re.findall(r'\b\d+\b', text)
    if numbers:
        return int(numbers[0])
    
    # 2. Buscar palabras de números en el idioma
    reverse_map = get_reverse_map(lang)
    text_lower = text.lower().strip()
    
    # Buscar coincidencias exactas
    if text_lower in reverse_map:
        return reverse_map[text_lower]
    
    # Buscar palabras individuales en el texto
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in reverse_map:
            return reverse_map[word]
    
    # 3. Búsqueda flexible (sin tildes, sin guiones)
    text_normalized = text_lower.replace("-", " ").replace("_", " ")
    words_normalized = text_normalized.split()
    for word in words_normalized:
        if word in reverse_map:
            return reverse_map[word]
    
    return None


def number_to_words(number: int, lang: str = "es") -> str:
    """
    Convierte número a palabras en el idioma especificado.
    
    Args:
        number: Número a convertir
        lang: Código de idioma
    
    Returns:
        Texto en palabras o el número como string si no está en el diccionario
    """
    words_map = NUMBER_WORDS.get(lang, {})
    return words_map.get(number, str(number))


def get_supported_languages() -> List[str]:
    """Retorna lista de idiomas soportados."""
    return list(NUMBER_WORDS.keys())