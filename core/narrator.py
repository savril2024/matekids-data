"""
core/narrator.py
Narrador usando la capa de plataforma.
Si Flet cambia, solo modificamos platform.py.
"""
import flet as ft
from core.platform import get_platform


class Narrator:
    def __init__(self, lang="es", on_text=None):
        self.lang = lang
        self.on_text = on_text
        self.page = None

    def set_page(self, page: ft.Page):
        self.page = page
        print("✅ Narrator: usando PlatformContext")

    def speak(self, text: str):
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            return
        platform = get_platform(self.page, self.lang)
        self.page.run_task(platform.speak, text, self.lang, self.on_text)

    async def speak_and_wait(self, text: str, timeout_sec: float = None):
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            return
        
        platform = get_platform(self.page, self.lang)
        await platform.speak(text, self.lang, self.on_text)