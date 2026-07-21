import asyncio
import flet as ft
import random
import re
from core.narrator import Narrator
from core.translations import get_text

class ActivityEngine:
    """Motor ciego al contenido con soporte de voz para respuestas."""

    def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
        self.page = page
        self.data = activity
        self.on_finish = on_finish
        self.lang = lang
        self.lang_code = "es-ES" if lang == "es" else "en-US"
        self.is_listening = False

        # 🔊 Audio para narración
        self.audio = ft.Audio(src="", autoplay=False, on_loaded=lambda _: None)
        page.overlay.append(self.audio)

        self.narrator = Narrator(lang=lang, on_text=self._show_subtitle)
        self.narrator.set_page(page)

        # 🎨 Elementos de la UI
        self.subtitle = ft.Text("", size=22, italic=True, color=ft.Colors.BLUE_GREY_700, text_align=ft.TextAlign.CENTER, width=600)
        self.objects_view = ft.Row(wrap=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)
        
        # 🎙️ Campo oculto para recibir el texto del navegador
        self.voice_input = ft.TextField(visible=False, on_change=self._process_voice_answer)

    def build(self) -> ft.Control:
        title_text = self.data["title"]
        if isinstance(title_text, dict):
            title_text = title_text.get(self.lang, title_text.get("es", ""))

        return ft.Stack([
            ft.Column([
                ft.Text(title_text, size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
                ft.Container(height=20),
                self.objects_view,
                ft.Container(height=20),
                self.subtitle,
                self.feedback,
                ft.Container(height=10),
                self._build_options(),
                self.voice_input, # Campo oculto para la magia de JS
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            self.confetti_layer
        ], expand=True)

    def _text_to_number(self, text: str) -> int | None:
        """Convierte texto hablado ('cinco', 'five', '25') a un número entero."""
        text = text.lower().strip()
        
        # 1. Intentar encontrar un dígito directamente (ej: "la respuesta es 5")
        digit_match = re.search(r'\d+', text)
        if digit_match:
            return int(digit_match.group())
        
        # 2. Diccionarios de palabras a números (0-30)
        words_es = {"cero":0, "uno":1, "dos":2, "tres":3, "cuatro":4, "cinco":5, "seis":6, "siete":7, "ocho":8, "nueve":9, "diez":10, "once":11, "doce":12, "trece":13, "catorce":14, "quince":15, "dieciseis":16, "diecisiete":17, "dieciocho":18, "diecinueve":19, "veinte":20, "veintiuno":21, "veintidos":22, "veintitres":23, "veinticuatro":24, "veinticinco":25, "veintiseis":26, "veintisiete":27, "veintiocho":28, "veintinueve":29, "treinta":30}
        words_en = {"zero":0, "one":1, "two":2, "three":3, "four":4, "five":5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10, "eleven":11, "twelve":12, "thirteen":13, "fourteen":14, "fifteen":15, "sixteen":16, "seventeen":17, "eighteen":18, "nineteen":19, "twenty":20, "twenty-one":21, "twenty-two":22, "twenty-three":23, "twenty-four":24, "twenty-five":25, "twenty-six":26, "twenty-seven":27, "twenty-eight":28, "twenty-nine":29, "thirty":30}
        
        dictionary = words_es if self.lang == "es" else words_en
        
        # Limpiar texto de puntuación
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        # Buscar coincidencia exacta o parcial
        for word, num in dictionary.items():
            if word in clean_text:
                return num
                
        return None

    def _start_listening(self, e):
        """Activa el micrófono del navegador."""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.feedback.value = "🎙️ ¡Te escucho! Habla ahora..."
        self.feedback.color = ft.Colors.RED
        self.page.update()

        # Inyectar JavaScript para usar el micrófono del navegador
        js_code = f"""
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = '{self.lang_code}';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        recognition.onresult = (event) => {{
            const text = event.results[0][0].transcript;
            // Buscar el input oculto de Flet y disparar el evento 'change'
            const inputs = document.querySelectorAll('input');
            for (let input of inputs) {{
                if (input.getAttribute('data-flet-id') === '{self.voice_input.uid}') {{
                    input.value = text;
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    break;
                }}
            }}
        }};
        
        recognition.onerror = (event) => {{
            console.error('Error de voz:', event.error);
        }};
        
        recognition.onend = () => {{
            // Notificar a Python que terminó de escuchar
            window.dispatchEvent(new CustomEvent('flet-event', {{ detail: {{ name: 'voice_ended', data: '' }} }}));
        }};
        
        recognition.start();
        """
        self.page.evaluate(js_code)

    def _on_voice_ended(self, e):
        """Se ejecuta cuando el navegador deja de escuchar."""
        self.is_listening = False
        self.feedback.value = ""
        self.page.update()

    def _process_voice_answer(self, e):
        """Procesa el texto recibido del navegador."""
        spoken_text = e.control.value
        self.is_listening = False
        self.feedback.value = "" # Limpiar "Te escucho..."
        
        number = self._text_to_number(spoken_text)
        
        if number is not None:
            self.subtitle.value = f'Dijiste: "{spoken_text}" ({number})'
            self._check(number)
        else:
            self.subtitle.value = f'Dijiste: "{spoken_text}"'
            self.feedback.value = "🤔 No entendí el número. ¡Intenta de nuevo!"
            self.feedback.color = ft.Colors.ORANGE
            self.narrator.speak("No entendí el número. Intenta de nuevo." if self.lang == "es" else "I didn't catch the number. Try again.")
            self.page.update()

    def _check(self, value: int):
        correct = value == self.data["answer"]
        if correct:
            self.feedback.value = get_text(self.lang, "very_good")
            self.feedback.color = ft.Colors.GREEN
            self._launch_confetti()
            self.narrator.speak(f"{get_text(self.lang, 'very_good').replace('⭐', '').strip()} {self.data['answer']}.")
            self.on_finish(success=True, stars=1)
        else:
            self.feedback.value = get_text(self.lang, "try_again")
            self.feedback.color = ft.Colors.ORANGE
            self.narrator.speak(get_text(self.lang, "almost"))
            self.on_finish(success=False, stars=0)

    # ... [MANTÉN TODOS LOS DEMÁS MÉTODOS IGUAL: _reset, _make_emoji, _render_objects, _render_groups, _animate_*, _build_options, _launch_confetti, _clear_confetti, _show_subtitle, _speak, _wait] ...
    # (Solo asegúrate de que _build_options incluya el botón del micrófono, ver abajo)

    def _build_options(self) -> ft.Control:
        col = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        # Fila de botones numéricos
        row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        for opt in self.data["options"]:
            row.controls.append(
                ft.Button(
                    content=ft.Text(str(opt), size=34, weight=ft.FontWeight.BOLD),
                    width=90, height=90,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), bgcolor=ft.Colors.BLUE_100, color=ft.Colors.BLACK),
                    on_click=lambda e, v=opt: self._check(v)
                )
            )
        col.controls.append(row)
        
        # Botón de Micrófono
        mic_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=30),
                ft.Text("Responder con tu voz", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            width=280,
            height=60,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), bgcolor=ft.Colors.DEEP_PURPLE),
            on_click=self._start_listening
        )
        col.controls.append(mic_btn)
        
        return col

    # ... [Asegúrate de incluir _launch_confetti, _clear_confetti, _show_subtitle, _speak, _wait tal como los tenías] ...
    
    async def run(self):
        self._reset()
        op = self.data["operation"]
        narration = self.data["narration"]
        if isinstance(narration, dict) and self.lang in narration:
            narration = narration[self.lang]
        elif isinstance(narration, dict) and "es" in narration:
            narration = narration["es"]

        if op in ("+", "-"): self._render_objects(self.data["total"])
        elif op == "×": self._render_groups(self.data["groups"], self.data["per_group"])
        elif op == "÷": self._render_objects(self.data["total"])

        await self._wait(300)
        await self._speak(narration.get("intro", ""))
        await self._wait(500)

        if op == "-": await self._animate_remove(self.data["remove"])
        elif op == "+": await self._animate_add(self.data["add"])
        elif op == "×": await self._animate_multiply()
        elif op == "÷": await self._animate_divide(self.data["divisor"])

        await self._speak(narration.get("action", ""))
        await self._wait(400)
        await self._speak(narration.get("question", ""))