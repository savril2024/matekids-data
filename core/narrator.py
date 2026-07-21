import flet as ft

class Narrator:
    """Narrador usando Web Speech API (sin ft.Audio)."""
    
    def __init__(self, lang="es", on_text=None):
        self.lang = "es-ES" if lang == "es" else "en-US"
        self.on_text = on_text
        self.page = None

    def set_page(self, page: ft.Page):
        self.page = page

    def speak(self, text: str):
        if self.on_text:
            self.on_text(text)
        
        if not self.page:
            print(f"[NARRATOR] {text}")
            return

        # Usar Web Speech API del navegador
        js_code = f"""
        if ('speechSynthesis' in window) {{
            // Cancelar audio anterior
            window.speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance("{text.replace('"', '\\"')}");
            utterance.lang = "{self.lang}";
            utterance.rate = 0.9;  // Un poco más lento
            utterance.pitch = 1.1; // Un poco más agudo
            
            window.speechSynthesis.speak(utterance);
        }} else {{
            console.log('Web Speech API no soportada');
        }}
        """
        self.page.evaluate(js_code)