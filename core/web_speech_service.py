"""
core/web_speech_service.py
Servicio de voz usando Web Speech API del navegador.
Funciona en Flet Web, PWA y Render sin dependencias externas.
"""
import asyncio
import flet as ft
from core.speech_service import BaseSpeechService
from typing import Optional


class WebSpeechService(BaseSpeechService):
    """Usa Web Speech API nativa del navegador."""

    def __init__(self, page: ft.Page, lang: str = "es"):
        super().__init__(page, lang)
        self.browser_lang = "es-ES" if lang == "es" else "en-US"
        self._result_event = asyncio.Event()
        self._recognized_text: Optional[str] = None
        self._inject_web_speech_script()

    def _inject_web_speech_script(self):
        """Inyecta el script de Web Speech API en el navegador."""
        js_code = """
        (function() {
            if (window.MateKidsSpeech) return;
            
            window.MateKidsSpeech = {
                recognition: null,
                isListening: false,
                
                init: function(lang) {
                    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                        return false;
                    }
                    
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    this.recognition = new SpeechRecognition();
                    this.recognition.lang = lang;
                    this.recognition.continuous = false;
                    this.recognition.interimResults = false;
                    this.recognition.maxAlternatives = 1;
                    
                    this.recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        window.MateKidsSpeech._onResult(transcript);
                    };
                    
                    this.recognition.onerror = function(event) {
                        window.MateKidsSpeech._onError(event.error);
                    };
                    
                    this.recognition.onend = function() {
                        window.MateKidsSpeech.isListening = false;
                        window.MateKidsSpeech._onEnd();
                    };
                    
                    return true;
                },
                
                start: function() {
                    if (this.recognition && !this.isListening) {
                        this.isListening = true;
                        this.recognition.start();
                        return true;
                    }
                    return false;
                },
                
                stop: function() {
                    if (this.recognition && this.isListening) {
                        this.recognition.stop();
                        return true;
                    }
                    return false;
                },
                
                _onResult: function(text) {
                    if (window.flet) {
                        window.flet.invokeMethod('speech_result', {text: text});
                    }
                },
                
                _onError: function(error) {
                    if (window.flet) {
                        window.flet.invokeMethod('speech_error', {error: error});
                    }
                },
                
                _onEnd: function() {
                    if (window.flet) {
                        window.flet.invokeMethod('speech_end', {});
                    }
                }
            };
            
            window.MateKidsSpeech.init('es-ES');
        })();
        """
        
        try:
            if hasattr(self.page, 'run_js'):
                self.page.run_js(js_code)
        except Exception as e:
            print(f"⚠️ No se pudo inyectar Web Speech API: {e}")

    async def listen(self, timeout_ms: int = 6000) -> Optional[str]:
        """Escucha voz usando Web Speech API."""
        if self.on_start:
            self.on_start()
        
        self.state = "listening"
        self._result_event = asyncio.Event()
        self._recognized_text = None
        
        js_start = f"""
        (function() {{
            if (window.MateKidsSpeech && window.MateKidsSpeech.recognition) {{
                window.MateKidsSpeech.recognition.lang = '{self.browser_lang}';
                return window.MateKidsSpeech.start();
            }}
            return false;
        }})();
        """
        
        try:
            if hasattr(self.page, 'run_js'):
                result = await self.page.run_js(js_start)
                if not result:
                    if self.on_error:
                        self.on_error("not_supported")
                    return None
        except Exception as e:
            if self.on_error:
                self.on_error(f"js_error: {e}")
            return None
        
        try:
            await asyncio.wait_for(self._result_event.wait(), timeout=timeout_ms / 1000)
        except asyncio.TimeoutError:
            self.state = "timeout"
            if self.on_timeout:
                self.on_timeout()
            await self.stop()
            return None
        
        self.state = "finished"
        if self.on_result and self._recognized_text:
            self.on_result(self._recognized_text)
        
        return self._recognized_text

    async def start(self, timeout_ms: int = 6000) -> None:
        await self.listen(timeout_ms=timeout_ms)

    async def stop(self) -> None:
        js_stop = """
        (function() {
            if (window.MateKidsSpeech && window.MateKidsSpeech.recognition) {
                return window.MateKidsSpeech.stop();
            }
            return false;
        })();
        """
        
        try:
            if hasattr(self.page, 'run_js'):
                await self.page.run_js(js_stop)
        except Exception:
            pass
        
        self.state = "idle"
        if self.on_stop:
            self.on_stop()

    def handle_result(self, text: str):
        self._recognized_text = text
        self._result_event.set()

    def handle_error(self, error: str):
        self._recognized_text = None
        self._result_event.set()

    def handle_end(self):
        if not self._result_event.is_set():
            self._result_event.set()