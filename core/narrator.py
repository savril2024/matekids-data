import flet as ft

class Narrator:
    """Usa la síntesis de voz nativa del navegador (100% compatible con Render Web)."""

    def __init__(self, lang="es", audio_control=None, on_text=None):
        self.lang = "es-ES" if lang == "es" else "en-US"
        self.on_text = on_text
        self.page = None # Se inyectará desde el engine

    def set_page(self, page: ft.Page):
        self.page = page

    def speak(self, text: str):
        if self.on_text:
            self.on_text(text)
        
        if not self.page:
            print(f"[NARRATOR] {text}")
            return

        # Inyectar JavaScript para usar la voz del navegador
        # Esto evita problemas de archivos locales en Render
        js_code = f"""
        const utterance = new SpeechSynthesisUtterance("{text.replace('"', '\\"')}");
        utterance.lang = "{self.lang}";
        utterance.rate = 0.9; // Un poco más lento para niños
        utterance.pitch = 1.1; // Un poco más agudo, más amigable
        window.speechSynthesis.cancel(); // Detener audio anterior
        window.speechSynthesis.speak(utterance);
        """
        self.page.evaluate(js_code)