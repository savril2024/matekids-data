"""
core/dummy_speech_service.py
Servicio de voz dummy para cuando no hay micrófono disponible.
"""
import asyncio
from core.speech_service import BaseSpeechService
from typing import Optional


class DummySpeechService(BaseSpeechService):
    """Servicio dummy que no hace nada, solo notifica que no hay voz."""

    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        print("⚠️ Voz no disponible en este entorno")
        if self.on_error:
            self.on_error("not_supported")
        return None

    async def start(self, timeout_ms: int = 6000) -> None:
        await self.listen(timeout_ms=timeout_ms)

    async def stop(self) -> None:
        pass