import flet as ft

class Narrator:
    def __init__(self, lang="es", audio_control=None, on_text=None):
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

        js_code = f"""
        const utterance = new SpeechSynthesisUtterance("{text.replace('"', '\\"')}");
        utterance.lang = "{self.lang}";
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
        """
        self.page.evaluate(js_code)