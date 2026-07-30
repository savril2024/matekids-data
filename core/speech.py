"""
core/speech.py
Reconocimiento de voz (STT) - Compatible con Web (Render) y Desktop.
En web: usa solo botones (flet_audio_recorder no compatible con Flet 0.86.2 web)
En desktop: puede usar flet_audio_recorder si está instalado.
"""
from typing import Callable, Optional
import asyncio
import flet as ft
import os
from gtts import gTTS
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
        # Callbacks
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None
        # TextField para dictado (se crea en build_voice_input)
        self.voice_input: Optional[ft.TextField] = None
        
        # Carpeta para audio de confirmación
        self.audio_dir = os.path.join("assets", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)

    def set_page(self, page: ft.Page) -> None:
        self.page = page

    def set_language(self, lang: str) -> None:
        self.lang = lang

    def build_voice_input(self) -> ft.TextField:
        """
        Crea un TextField optimizado para dictado por voz.
        El niño toca este campo y luego el micrófono de su teclado.
        """
        self.voice_input = ft.TextField(
            label="🎤 Toca aquí y usa el micrófono de tu teclado",
            hint_text="Dicta el número...",
            text_size=24,
            text_align=ft.TextAlign.CENTER,
            multiline=False,
            keyboard_type=ft.KeyboardType.TEXT,
            on_change=self._on_text_changed,
            on_submit=self._on_submit,
            width=400,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE,
            bgcolor=ft.Colors.BLUE_50,
        )
        return self.voice_input
    
    def _on_text_changed(self, e):
        """Se dispara cada vez que el texto cambia (dictado en progreso)."""
        text = e.control.value.strip()
        if text:
            # Intentar parsear el número en tiempo real
            number = text_to_number(text, self.lang)
            if number is not None:
                # Número detectado, procesar respuesta
                self.state = SpeechState.TRANSCRIBED
                if self.on_result:
                    self.on_result(text)
    
    def _on_submit(self, e):
        """Se dispara cuando el usuario presiona Enter."""
        text = e.control.value.strip()
        if text:
            number = text_to_number(text, self.lang)
            if number is not None:
                self.state = SpeechState.TRANSCRIBED
                if self.on_result:
                    self.on_result(text)
            else:
                self.state = SpeechState.ERROR
                if self.on_error:
                    self.on_error("no_number_found")
    
    async def speak_confirmation(self, text: str, number: int):
        """
        Confirma la respuesta por voz usando gTTS.
        Ejemplo: "¡Muy bien! Cinco."
        """
        try:
            # Generar texto de confirmación
            number_words = number_to_words(number, self.lang)
            confirmation_text = f"¡Muy bien! {number_words}."
            
            # Generar audio con gTTS
            key = f"{self.lang}_{confirmation_text}"
            filename = hashlib.md5(key.encode("utf-8")).hexdigest() + ".mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            if not os.path.exists(filepath):
                tts = gTTS(text=confirmation_text, lang=self.lang)
                tts.save(filepath)
            
            # Reproducir audio (usando platform.py si está disponible)
            try:
                from core.platform import get_platform
                platform = get_platform(self.page, self.lang)
                await platform.speak(confirmation_text, self.lang)
            except ImportError:
                # Fallback: solo mostrar subtítulo
                print(f"[SPEECH] {confirmation_text}")
                
        except Exception as e:
            print(f"⚠️ Error en speak_confirmation: {e}")


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