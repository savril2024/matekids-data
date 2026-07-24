"""
core/narrator.py
Narrador por subtítulos con tiempos de lectura automáticos.
100% estable, sin dependencias de audio.
Funciona igual en desktop y web (Render).
"""
import asyncio
import flet as ft


class Narrator:
    """
    Muestra el texto como subtítulo y espera el tiempo necesario
    para que el niño lo lea (~350ms por palabra, mínimo 2.5 segundos).
    """

    def __init__(self, lang="es", on_text=None):
        self.lang = lang
        self.on_text = on_text
        self.page = None

    def set_page(self, page: ft.Page):
        self.page = page
        print("✅ Narrator: modo subtítulos (sin audio)")

    def speak(self, text: str):
        """Dispara la narración sin esperar (fire-and-forget)."""
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            print(f"[NARRATOR] {text}")
            return
        self.page.run_task(self._speak_async, text)

    async def speak_and_wait(self, text: str, timeout_sec: float = None):
        """
        Muestra el subtítulo y espera tiempo de lectura.
        Si timeout_sec no se especifica, se calcula automáticamente:
        - ~350ms por palabra
        - Mínimo 2.5 segundos
        - Máximo 8 segundos (para frases largas)
        """
        if self.on_text:
            self.on_text(text)
        if not self.page or not text:
            print(f"[NARRATOR] {text}")
            return
        
        # Calcular tiempo de lectura
        if timeout_sec is None:
            words = len(text.split())
            # 350ms por palabra, mínimo 2.5s, máximo 8s
            timeout_sec = max(2.5, min(8.0, words * 0.35))
        
        print(f"[NARRATOR] {text} ({timeout_sec:.1f}s)")
        await asyncio.sleep(timeout_sec)

    async def _speak_async(self, text: str):
        """Versión fire-and-forget."""
        await self.speak_and_wait(text)