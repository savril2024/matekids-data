"""
core/speech_service.py
Interfaz abstracta para servicios de reconocimiento de voz.
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional


class BaseSpeechService(ABC):
    """Interfaz común para todos los servicios de voz."""
    
    def __init__(self, page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self.state = "idle"
        
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None

    @abstractmethod
    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        pass

    @abstractmethod
    async def start(self, timeout_ms: int = 6000) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    def set_page(self, page) -> None:
        self.page = page

    def set_language(self, lang: str) -> None:
        self.lang = lang