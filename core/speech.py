"""
core/speech.py
Reconocimiento de voz (STT) - DESACTIVADO de forma segura.
Flet 0.86.2 rompió la compatibilidad con flet-audio-recorder 
(error: Unknown control: AudioRecorder).
La app funcionará perfectamente usando los botones de respuesta.
"""
import asyncio
from typing import Callable, Optional
import flet as ft

# Importar el parser de números para mantener compatibilidad
from core.number_parser import text_to_number  # noqa: F401


class SpeechState:
    IDLE = "idle"
    ERROR = "error"
    NOT_SUPPORTED = "not_supported"


class SpeechService:
    """
    Servicio de voz desactivado temporalmente por incompatibilidad 
    con Flet 0.86.2. No crashea la app, solo notifica que no está disponible.
    """

    def __init__(self, page: ft.Page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self.browser_lang = "es-ES" if lang == "es" else "en-US"
        self.state: str = SpeechState.IDLE

        # Callbacks (mantenemos la misma API para no romper engine.py)
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None

    def set_page(self, page: ft.Page) -> None:
        self.page = page

    def set_language(self, lang: str) -> None:
        self.lang = lang
        self.browser_lang = "es-ES" if lang == "es" else "en-US"

    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        """
        Simula la escucha y devuelve None inmediatamente.
        Dispara el callback de error para informar a la UI.
        """
        print("⚠️ Voz desactivada: flet-audio-recorder no es compatible con Flet 0.86.2")
        
        self.state = SpeechState.NOT_SUPPORTED
        
        if self.on_start:
            self.on_start()
            
        # Simular un pequeño delay para que la UI muestre el estado de "escuchando"
        await asyncio.sleep(0.5)
        
        if self.on_error:
            self.on_error("not_supported")
            
        return None

    async def start(self, timeout_ms: int = 6000) -> None:
        """Alias de listen()."""
        await self.listen(timeout_ms=timeout_ms)

    async def stop(self) -> None:
        """Detiene la operación (no-op en este caso)."""
        self.state = SpeechState.IDLE
        if self.on_stop:
            self.on_stop()


# Compatibilidad hacia atrás para imports antiguos
SpeechRecognizer = SpeechService

# # """
# # core/speech.py
# # Reconocimiento de voz (STT) - DESHABILITADO temporalmente.
# # Flet 0.86+ no permite ejecutar JavaScript directamente.
# # Se usará solo entrada manual por botones.
# # """
# from typing import Callable, Optional
# import uuid
# # El parser de numeros vive en su propio modulo, independiente de Flet.
# # Se re-exporta aqui para no romper imports existentes
# # ("from core.speech import SpeechRecognizer, text_to_number").
# from core.number_parser import  text_to_number  # noqa: F401
# import asyncio
# import uuid
# from pathlib import Path
# import flet as ft
# from flet_audio_recorder import (
#     AudioRecorder,
#     AudioRecorderConfiguration,
#     AudioRecorderUploadSettings,
#     AudioRecorderUploadEvent,
#     AudioEncoder,
# )


# class SpeechState:
#     #""Estados posibles del servicio."""
#     IDLE = "idle"
#     RECORDING = "recording"
#     UPLOADING = "uploading"
#     TRANSCRIBING = "transcribing"
#     FINISHED = "finished"
#     ERROR = "error"
#     TIMEOUT = "timeout"


# class SpeechService:
#     """
     
#     Graba con el microfono del navegador (AudioRecorder) y transcribe
#     el audio a texto en el servidor (SpeechRecognition). No conoce
#     nada de matematicas ni de UI del juego: solo entrega texto.
#     """

#      # Debe coincidir EXACTAMENTE con upload_dir= pasado a ft.run(...)

#     UPLOAD_DIR_NAME = "uploads"

#     def __init__(self, page: ft.Page, lang: str = "es"):
#         self.page = page
#         self.lang = lang
#         self.browser_lang = "es-ES" if lang == "es" else "en-US"
#         self.state: str = SpeechState.IDLE

#     # Eventos (callbacks opcionales, mismo estilo que la version anterior)
    
#         self.on_result: Optional[Callable[[str], None]] = None
#         self.on_error: Optional[Callable[[str], None]] = None
#         self.on_start: Optional[Callable[[], None]] = None
#         self.on_stop: Optional[Callable[[], None]] = None
#         self.on_timeout: Optional[Callable[[], None]] = None
#         self._upload_event = asyncio.Event()
#         self._upload_error: Optional[str] = None

#         self.recorder = AudioRecorder(
#             configuration=AudioRecorderConfiguration(encoder=AudioEncoder.WAV),
#             on_upload=self._on_upload,
#         )
#         self._attach_recorder()
#     # ------------------------------------------------------------
#     # Configuracion
#     # ------------------------------------------------------------
#     def _attach_recorder(self) -> None:
#         """El AudioRecorder necesita vivir en page.overlay para funcionar."""
#         if self.page and self.recorder not in self.page.overlay:
#             self.page.overlay.append(self.recorder)
#             self.page.update()

#     def set_page(self, page: ft.Page) -> None:
#         """Compatibilidad con el patron set_page() usado por Narrator."""
#         self.page = page
#         self._attach_recorder()

#     def set_language(self, lang: str) -> None:
#         """Acepta 'es'/'en' cortos y los traduce al codigo que espera SpeechRecognition."""
#         self.lang = lang
#         self.recognizer_lang = "es-ES" if lang == "es" else "en-US"

#     # ------------------------------------------------------------
#     # Callback interno de subida
#     # ------------------------------------------------------------
#     def _on_upload(self, e: AudioRecorderUploadEvent) -> None:
#         if e.error:
#             self._upload_error = e.error
#             self._upload_event.set()
#         elif e.progress is not None and e.progress >= 1.0:
#             self._upload_event.set()

#     # ------------------------------------------------------------
#     # API principal
#     # ------------------------------------------------------------
#     async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
#         """
#         Graba hasta timeout_ms, sube el audio y lo transcribe.
#         Devuelve el texto reconocido, o None si hubo timeout/error.
#         Dispara on_start/on_result/on_error/on_timeout en el camino.
#         """
#         if not self.page:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error("no_page")
#             return None

#         self.state = SpeechState.RECORDING
#         if self.on_start:
#             self.on_start()

#         try:
#             has_perm = await self.recorder.has_permission()
#         except Exception:
#             # Algunos entornos no exponen bien el chequeo; seguimos e
#             # dejamos que start_recording() falle mas abajo si de
#             # verdad no hay permiso.
#             has_perm = True

#         if not has_perm:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error("not-allowed")
#             return None

#         self._upload_event = asyncio.Event()
#         self._upload_error = None
#         filename = f"speech_{uuid.uuid4().hex}.wav"

#         try:
#             upload_url = self.page.get_upload_url(filename, expires=600)
#         except Exception as ex:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error(f"upload_url_failed: {ex}")
#             return None

#         upload_settings = AudioRecorderUploadSettings(
#             upload_url=upload_url,
#             file_name=filename,
#         )

#         try:
#             started = await self.recorder.start_recording(upload=upload_settings)
#         except Exception as ex:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error(f"start_failed: {ex}")
#             return None

#         if not started:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error("start_failed")
#             return None

#         # Graba durante timeout_ms (no hay deteccion de silencio en
#         # AudioRecorder; a diferencia del Web Speech API antiguo, aqui
#         # grabamos un tramo de duracion fija).
#         await asyncio.sleep(timeout_ms / 1000)

#         self.state = SpeechState.UPLOADING
#         try:
#             await self.recorder.stop_recording()
#         except Exception:
#             pass

#         try:
#             await asyncio.wait_for(self._upload_event.wait(), timeout=10)
#         except asyncio.TimeoutError:
#             self.state = SpeechState.TIMEOUT
#             if self.on_timeout:
#                 self.on_timeout()
#             return None

#         if self._upload_error:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error(self._upload_error)
#             return None

#         self.state = SpeechState.TRANSCRIBING
#         text = await asyncio.to_thread(self._transcribe, filename)

#         if text is None:
#             self.state = SpeechState.ERROR
#             if self.on_error:
#                 self.on_error("no-speech")
#             return None

#         self.state = SpeechState.FINISHED
#         if self.on_result:
#             self.on_result(text)
#         return text

#     async def start(self, timeout_ms: int = 6000) -> None:
#         """Alias de listen(), para quien prefiera el patron start()/stop()."""
#         await self.listen(timeout_ms=timeout_ms)

#     async def stop(self) -> None:
#         """Detiene la grabacion en curso, si la hay."""
#         try:
#             await self.recorder.stop_recording()
#         except Exception:
#             pass
#         self.state = SpeechState.IDLE
#         if self.on_stop:
#             self.on_stop()

#     # ------------------------------------------------------------
#     # Transcripcion (corre en un hilo aparte: es una llamada de red bloqueante)
#     # ------------------------------------------------------------
#     def _transcribe(self, filename: str) -> Optional[str]:
#         import speech_recognition as sr

#         audio_path = self._resolve_upload_path(filename)
#         if not audio_path or not audio_path.exists():
#             print(f"[SpeechService] No se encontro el archivo subido: {audio_path}")
#             return None

#         recognizer = sr.Recognizer()
#         try:
#             with sr.AudioFile(str(audio_path)) as source:
#                 audio_data = recognizer.record(source)
#             return recognizer.recognize_google(audio_data, language=self.recognizer_lang)
#         except sr.UnknownValueError:
#             return None
#         except Exception as ex:
#             print(f"[SpeechService] Error transcribiendo: {ex}")
#             return None
#         finally:
#             try:
#                 audio_path.unlink(missing_ok=True)
#             except Exception:
#                 pass

#     def _resolve_upload_path(self, filename: str) -> Optional[Path]:
#         """
#         Ubica el archivo subido dentro del upload_dir configurado en
#         ft.run(...). Flet lo guarda como <upload_dir>/<filename>.
#         Ajusta UPLOAD_DIR_NAME si usas otro nombre de carpeta.
#         """
#         base_dir = Path(__file__).resolve().parent.parent  # raiz del proyecto
#         return base_dir / self.UPLOAD_DIR_NAME / filename


# # ==========================================
# # COMPATIBILIDAD HACIA ATRAS
# # ==========================================
# # engine.py importa "SpeechRecognizer" (el nombre anterior). Se deja
# # como alias para no tener que tocar sus imports.
# SpeechRecognizer = SpeechService

