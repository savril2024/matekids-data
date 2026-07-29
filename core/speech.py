"""
core/speech.py
Reconocimiento de voz usando la capa de plataforma.
Sin imports de flet_audio_recorder (que rompe en web).
"""
from typing import Callable, Optional
import flet as ft
from core.platform import get_platform
from core.number_parser import text_to_number  # noqa: F401


class SpeechState:
    IDLE = "idle"
    NOT_SUPPORTED = "not_supported"
    ERROR = "error"


class SpeechService:
    def __init__(self, page: ft.Page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self.state = SpeechState.IDLE
        
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None

    def set_page(self, page: ft.Page):
        self.page = page

    def set_language(self, lang: str):
        self.lang = lang

    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        print("⚠️ SpeechService: voz no disponible (usar botones)")
        self.state = SpeechState.NOT_SUPPORTED
        if self.on_start:
            self.on_start()
        if self.on_error:
            self.on_error("not_supported")
        return None

    async def start(self, timeout_ms: int = 6000):
        await self.listen(timeout_ms)

    async def stop(self):
        self.state = SpeechState.IDLE
        if self.on_stop:
            self.on_stop()


SpeechRecognizer = SpeechService