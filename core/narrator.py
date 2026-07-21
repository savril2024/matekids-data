import os
import tempfile
import threading
import time  # <-- AGREGAR ESTO
from pathlib import Path


try:
    import importlib
    _gtts = importlib.import_module("gtts")
    gTTS = _gtts.gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# Carpeta temporal para MP3 (Render tiene /tmp writable)
AUDIO_DIR = Path(tempfile.gettempdir()) / "matekids_audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class Narrator:
    """Genera MP3 con gTTS y lo reproduce con ft.Audio de Flet (funciona en web)."""

    def __init__(self, lang="es", audio_control=None, on_text=None):
        self.lang = lang
        self.audio_control = audio_control  # ft.Audio inyectado desde engine
        self.on_text = on_text
        self._counter = 0

    def speak(self, text: str):
        if self.on_text:
            self.on_text(text)

        if not HAS_GTTS or not self.audio_control:
            print(f"[NARRATOR] {text}")
            return

        threading.Thread(target=self._generate_and_play,
                         args=(text,), daemon=True).start()

    def _generate_and_play(self, text: str):
        try:
            self._counter += 1
            # CAMBIO CLAVE: Usar timestamp para que el nombre sea único y Windows no lo bloquee

            filename = AUDIO_DIR / f"narration_{int(time.time() * 3000)}.mp3"

            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(str(filename))

            # ft.Audio reproduce en el navegador (funciona en web)
            self.audio_control.src = str(filename)
            self.audio_control.autoplay = True
            self.audio_control.update()
        except Exception as e:
            print(f"[NARRATOR ERROR] {e}")
