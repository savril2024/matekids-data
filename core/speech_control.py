"""
core/speech_control.py
Componente de reconocimiento de voz para Flet 0.86+.
Usa la API moderna de Flet para comunicación con el navegador.
"""
import flet as ft
from typing import Callable, Optional

class SpeechControl:
    """Control de voz que usa la API oficial de Flet 0.86+."""
    
    def __init__(
        self, 
        page: ft.Page,
        lang: str = "es-ES",
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.page = page
        self.lang = lang
        self.on_result = on_result
        self.on_error = on_error
        self._is_listening = False
        
        # Campo oculto que recibe el texto del navegador
        self._hidden_input = ft.TextField(visible=False)
        self._controls = [self._hidden_input]
        
        # Registrar evento personalizado
        self.page.on_event = self._handle_event

    def build(self):
        """Método requerido por ft.Control en Flet 0.86+."""
        return self._hidden_input

    def _handle_event(self, e):
        """Maneja eventos personalizados desde JavaScript."""
        if e.event_name == "flet-speech-result":
            text = e.data
            self._is_listening = False
            
            if self.on_result:
                self.on_result(text)
        elif e.event_name == "flet-speech-error":
            error = e.data
            self._is_listening = False
            
            if self.on_error:
                self.on_error(error)

    def start_listening(self):
        """Inicia el reconocimiento de voz."""
        if self._is_listening or not self.page:
            return
        
        self._is_listening = True
        input_id = self._hidden_input.uid
        
        # Inyectar script directamente en la página
        js_code = f"""
        (function() {{
            if (!window.FletSpeech) {{
                const script = document.createElement('script');
                script.src = '/assets/js/speech.js';
                document.head.appendChild(script);
            }}
            
            window.FletSpeech.listenOnce({{
                lang: '{self.lang}',
                timeoutMs: 6000
            }});
        }})();
        """
        
        # Ejecutar JavaScript en el contexto de la página
        self.page.run_task(self._run_js, js_code)

    def _run_js(self, js_code: str):
        """Ejecuta JavaScript de forma segura."""
        if hasattr(self.page, 'run_js'):
            self.page.run_js(js_code)
        elif hasattr(self.page, 'evaluate'):
            self.page.evaluate(js_code)

    def stop_listening(self):
        """Detiene el reconocimiento de voz."""
        self._is_listening = False
        js_code = "if (window.FletSpeech) window.FletSpeech.stop();"
        
        if hasattr(self.page, 'run_js'):
            self.page.run_js(js_code)
        elif hasattr(self.page, 'evaluate'):
            self.page.evaluate(js_code)