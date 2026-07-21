import asyncio
import flet as ft
import random
import re
from core.narrator import Narrator
from core.translations import get_text

class ActivityEngine:
    def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
        self.page = page
        self.data = activity
        self.on_finish = on_finish
        self.lang = lang
        self.lang_code = "es-ES" if lang == "es" else "en-US"
        self.is_listening = False

        self.audio = ft.Audio(src="", autoplay=False, on_loaded=lambda _: None)
        page.overlay.append(self.audio)

        self.narrator = Narrator(lang=lang, on_text=self._show_subtitle)
        self.narrator.set_page(page)

        self.subtitle = ft.Text("", size=22, italic=True, color=ft.Colors.BLUE_GREY_700, text_align=ft.TextAlign.CENTER, width=600)
        self.objects_view = ft.Row(wrap=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)
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
                self.voice_input,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            self.confetti_layer
        ], expand=True)

    async def run(self):
        self._reset()
        op = self.data["operation"]

        narration = self.data["narration"]
        if isinstance(narration, dict) and self.lang in narration:
            narration = narration[self.lang]
        elif isinstance(narration, dict) and "es" in narration:
            narration = narration["es"]

        # Paso 1: Mostrar objetos
        if op in ("+", "-"):
            self._render_objects(self.data["total"])
        elif op == "×":
            self._render_groups(self.data["groups"], self.data["per_group"])
        elif op == "÷":
            self._render_objects(self.data["total"])

        await self._wait(500)
        await self._speak(narration.get("intro", ""))
        await self._wait(500)

        # Paso 2: ANIMACIÓN
        if op == "-":
            await self._animate_remove(self.data["remove"])
        elif op == "+":
            await self._animate_add(self.data["add"])
        elif op == "×":
            await self._animate_multiply()
        elif op == "÷":
            await self._animate_divide(self.data["divisor"])

        await self._speak(narration.get("action", ""))
        await self._wait(500)
        await self._speak(narration.get("question", ""))

    def _reset(self):
        self.objects_view.controls = []
        self.feedback.value = ""
        self.subtitle.value = ""
        self.confetti_layer.controls = []
        self.page.update()

    def _make_emoji(self, emoji: str, size: int = 40) -> ft.Image:
        emoji_codes = {
            "🍎": "1f34e", "🍕": "1f355", "🚗": "1f697", "🚕": "1f695",
            "🐟": "1f41f", "🐶": "1f436", "⭐": "2b50", "🎈": "1f388",
            "📚": "1f4da", "🎒": "1f392", "✏️": "270f", "📐": "1f4d0",
            "️": "1f58d", "": "1f3c6", "": "1f36a", "": "1f36c",
            "🌸": "1f338", "👩🦰": "1f469-1f3fb-200d-1f9b0"
        }
        code = emoji_codes.get(emoji, "1f34e")
        url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/{code}.svg"
        return ft.Image(src=url, width=size, height=size, fit=ft.ImageFit.CONTAIN, animate_scale=ft.Animation(400))

    def _render_objects(self, count: int):
        self.objects_view.controls.clear()
        for _ in range(count):
            self.objects_view.controls.append(self._make_emoji(self.data["emoji"]))
        self.page.update()

    def _render_groups(self, groups: int, per_group: int):
        self.objects_view.controls.clear()
        for _ in range(groups):
            group = ft.Row([self._make_emoji(self.data["emoji"], size=35) for _ in range(per_group)], spacing=3)
            self.objects_view.controls.append(group)
        self.page.update()

    async def _animate_remove(self, n: int):
        """Anima la remoción de objetos."""
        controls = self.objects_view.controls
        to_remove = controls[-n:] if len(controls) >= n else controls
        
        for obj in to_remove:
            obj.scale = 0.5
            obj.opacity = 0.3
            self.page.update()
            await self._wait(300)
        
        # Remover del todo
        for obj in to_remove:
            if obj in self.objects_view.controls:
                self.objects_view.controls.remove(obj)
        self.page.update()

    async def _animate_add(self, n: int):
        """Anima la adición de objetos."""
        for i in range(n):
            new_obj = self._make_emoji(self.data["emoji"])
            new_obj.scale = 0
            self.objects_view.controls.append(new_obj)
            self.page.update()
            await self._wait(100)
            
            # Animar crecimiento
            new_obj.scale = 1.2
            self.page.update()
            await self._wait(200)
            new_obj.scale = 1
            self.page.update()

    async def _animate_multiply(self):
        """Resalta cada grupo."""
        for group in self.objects_view.controls:
            if isinstance(group, ft.Row):
                for obj in group.controls:
                    obj.scale = 1.3
                self.page.update()
                await self._wait(400)
                for obj in group.controls:
                    obj.scale = 1
                self.page.update()

    async def _animate_divide(self, divisor: int):
        """Anima la división en grupos."""
        total = len(self.objects_view.controls)
        self.objects_view.controls.clear()
        
        # Crear contenedores vacíos
        containers = []
        for i in range(divisor):
            container = ft.Container(
                content=ft.Row(spacing=3, wrap=True),
                border=ft.border.all(2, ft.Colors.PURPLE),
                border_radius=10,
                padding=10,
                bgcolor=ft.Colors.PURPLE_50,
                width=100
            )
            containers.append(container)
            self.objects_view.controls.append(container)
        self.page.update()
        
        # Distribuir objetos
        objs = [self._make_emoji(self.data["emoji"]) for _ in range(total)]
        for i, obj in enumerate(objs):
            group_idx = i % divisor
            if isinstance(containers[group_idx].content, ft.Row):
                containers[group_idx].content.controls.append(obj)
            self.page.update()
            await self._wait(200)

    def _build_options(self) -> ft.Control:
        col = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
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
        
        mic_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=30),
                ft.Text("Responder con tu voz", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            width=280, height=60,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30), bgcolor=ft.Colors.DEEP_PURPLE),
            on_click=self._start_listening
        )
        col.controls.append(mic_btn)
        
        return col

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

    def _launch_confetti(self):
        emojis = ["🎉", "⭐", "🎊", "✨", "🌟"]
        for i in range(15):
            e = ft.Text(random.choice(emojis), size=32, top=-50, left=random.randint(20, 500))
            self.confetti_layer.controls.append(e)
        self.page.update()
        self.page.run_task(self._clear_confetti)

    async def _clear_confetti(self):
        await self._wait(1500)
        self.confetti_layer.controls = []
        self.page.update()

    def _text_to_number(self, text: str) -> int | None:
        text = text.lower().strip()
        digit_match = re.search(r'\d+', text)
        if digit_match:
            return int(digit_match.group())
        
        words_es = {"cero":0, "uno":1, "dos":2, "tres":3, "cuatro":4, "cinco":5, "seis":6, "siete":7, "ocho":8, "nueve":9, "diez":10, "once":11, "doce":12, "trece":13, "catorce":14, "quince":15, "dieciseis":16, "diecisiete":17, "dieciocho":18, "diecinueve":19, "veinte":20, "veintiuno":21, "veintidos":22, "veintitres":23, "veinticuatro":24, "veinticinco":25}
        words_en = {"zero":0, "one":1, "two":2, "three":3, "four":4, "five":5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10, "eleven":11, "twelve":12, "thirteen":13, "fourteen":14, "fifteen":15, "sixteen":16, "seventeen":17, "eighteen":18, "nineteen":19, "twenty":20, "twenty-one":21, "twenty-two":22, "twenty-three":23, "twenty-four":24, "twenty-five":25}
        
        dictionary = words_es if self.lang == "es" else words_en
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        for word, num in dictionary.items():
            if word in clean_text:
                return num
        return None

    def _start_listening(self, e):
        if self.is_listening:
            return
        self.is_listening = True
        self.feedback.value = "🎙️ ¡Te escucho! Habla ahora..."
        self.feedback.color = ft.Colors.RED
        self.page.update()

        js_code = f"""
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = '{self.lang_code}';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        recognition.onresult = (event) => {{
            const text = event.results[0][0].transcript;
            const inputs = document.querySelectorAll('input');
            for (let input of inputs) {{
                if (input.getAttribute('data-flet-id') === '{self.voice_input.uid}') {{
                    input.value = text;
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    break;
                }}
            }}
        }};
        
        recognition.start();
        """
        self.page.evaluate(js_code)

    def _process_voice_answer(self, e):
        spoken_text = e.control.value
        self.is_listening = False
        self.feedback.value = ""
        
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

    def _show_subtitle(self, text: str):
        self.subtitle.value = f'"{text}"'
        self.page.update()

    async def _speak(self, text: str):
        if text:
            self.narrator.speak(text)
            await self._wait(len(text) * 70)

    async def _wait(self, ms: int):
        await asyncio.sleep(ms / 1000)