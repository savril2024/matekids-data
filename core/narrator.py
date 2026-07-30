"""
core/narrator.py
Narrador en MODO SUBTÍTULOS para Render (Web).
100% estable: sin dependencias de audio, sin crashes.
"""
import asyncio
import flet as ft

class Narrator:
    def __init__(self, lang="es", on_text=None):
        self.lang = lang
        self.on_text = on_text
        self.page = None

    def set_page(self, page: ft.Page):
        self.page = page
        print("✅ Narrator: modo subtítulos activo (ideal para Render/Web)")

    def speak(self, text: str):
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            return
        self.page.run_task(self._speak_async, text)

    async def speak_and_wait(self, text: str, timeout_sec: float = None):
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            return
        
        if timeout_sec is None:
            words = len(text.split())
            timeout_sec = max(2.5, min(8.0, words * 0.35))
        
        print(f"[NARRATOR] {text} ({timeout_sec:.1f}s)")
        await asyncio.sleep(timeout_sec)

    async def _speak_async(self, text: str):
        await self.speak_and_wait(text)