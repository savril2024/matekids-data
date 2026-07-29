"""
core/speech.py
Reconocimiento de voz (STT) - Compatible con Web (Render) y Desktop.
En web: usa solo botones (flet_audio_recorder no compatible con Flet 0.86.2 web)
En desktop: puede usar flet_audio_recorder si está instalado.
"""
from typing import Callable, Optional
import asyncio
import flet as ft
from core.number_parser import text_to_number  # noqa: F401


class SpeechState:
    IDLE = "idle"
    ERROR = "error"
    NOT_SUPPORTED = "not_supported"


class SpeechService:
    """
    Servicio de voz simple que funciona en web y desktop.
    En web, solo notifica que no está disponible y usa botones.
    """

    def __init__(self, page: ft.Page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self.state: str = SpeechState.IDLE

        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None

    def set_page(self, page: ft.Page) -> None:
        self.page = page

    def set_language(self, lang: str) -> None:
        self.lang = lang

    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        """Simula la escucha y devuelve None. Dispara el callback de error."""
        print("⚠️ Voz desactivada: usando solo botones de respuesta")
        self.state = SpeechState.NOT_SUPPORTED
        
        if self.on_start:
            self.on_start()
        
        await asyncio.sleep(0.5)
        
        if self.on_error:
            self.on_error("not_supported")
        
        return None

    async def start(self, timeout_ms: int = 6000) -> None:
        """Alias de listen()."""
        await self.listen(timeout_ms=timeout_ms)

    async def stop(self) -> None:
        """Detiene la operación (no-op)."""
        self.state = SpeechState.IDLE
        if self.on_stop:
            self.on_stop()


def create_speech_service(page: ft.Page, lang: str = "es") -> SpeechService:
    """
    Factory que crea el servicio de voz apropiado según el entorno.
    Actualmente siempre retorna SpeechService simple (compatible con web y desktop).
    """
    return SpeechService(page, lang)


# Compatibilidad hacia atrás
SpeechRecognizer = SpeechService