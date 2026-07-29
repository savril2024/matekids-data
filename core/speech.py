"""
core/speech.py
Factory que selecciona el servicio de voz según disponibilidad.
Prioridad: WebSpeechService > DummyService
"""
from typing import Optional
import flet as ft
from core.speech_service import BaseSpeechService
from core.number_parser import text_to_number  # noqa: F401


def create_speech_service(page: ft.Page, lang: str = "es") -> BaseSpeechService:
    """
    Crea el servicio de voz más adecuado según el entorno.
    - Web/PWA: Usa WebSpeechService (nativo del navegador)
    - Fallback: DummyService (solo botones)
    """
    # Detectar si estamos en modo web
    is_web = (
        hasattr(page, 'session_id') or
        __import__('os').environ.get('FLET_VIEW') == 'web_browser'
    )
    
    if is_web:
        from core.web_speech_service import WebSpeechService
        print("✅ SpeechService: usando Web Speech API (navegador)")
        return WebSpeechService(page, lang)
    
    # Fallback: servicio dummy
    from core.dummy_speech_service import DummySpeechService
    print("⚠️ SpeechService: usando DummyService (solo botones)")
    return DummySpeechService(page, lang)


# Compatibilidad hacia atrás
SpeechService = create_speech_service
SpeechRecognizer = create_speech_service