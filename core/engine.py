
"""
core/engine.py
COORDINADOR PRINCIPAL.
Usa SpeechService factory para seleccionar implementación automáticamente.
"""
import asyncio
import flet as ft
from core.game_logic import GameLogic
from core.narrator import Narrator
from core.speech import SpeechService, create_speech_service
from core.number_parser import text_to_number
from core.visual_renderer import VisualRenderer
from core.animator import Animator
from core.ui_builder import UIBuilder
from core.translations import get_text


class ActivityEngine:
    def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
        self.page = page
        self.on_finish = on_finish
        self.lang = lang
        
        self.logic = GameLogic(activity, lang)
        self.visual_setup = self.logic.get_visual_setup()
        
        self.renderer = VisualRenderer()
        self.animator = Animator(self.renderer)
        self.ui_builder = UIBuilder()
        
        self.narrator = Narrator(lang=lang, on_text=self._show_subtitle)
        self.narrator.set_page(page)

        # ✅ NUEVO: Usar factory para crear el servicio de voz
        self.speech_service = create_speech_service(page, lang)
        self.speech_service.on_result = self._on_voice_result
        self.speech_service.on_error = self._on_voice_error
        self.speech_service.on_timeout = self._on_voice_timeout
        
        self.subtitle = ft.Text("", size=26, italic=True, color=ft.Colors.BLUE_GREY_700, 
                                text_align=ft.TextAlign.CENTER, width=600)
        self.objects_view = ft.Column(wrap=False, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)

        self.speech_service = create_speech_service(page, lang=lang)
        self.speech_service.on_result = self._on_voice_result
        self.speech_service.on_error = self._on_voice_error
        self.speech_service.on_timeout = self._on_voice_timeout

        self.subtitle = ft.Text(
            "", size=26, weight=ft.FontWeight.NORMAL,
            color=ft.Colors.BLUE_GREY_700, 
            text_align=ft.TextAlign.CENTER, width=600, italic=True
        )
        self.objects_view = ft.Column(
            wrap=False, spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)

    def build(self) -> ft.Control:
        return ft.Stack([
            ft.Column([
                ft.Text(self.logic.get_title(), size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
                ft.Container(height=20),
                self.objects_view,
                ft.Container(height=20),
                self.subtitle,
                self.feedback,
                ft.Container(height=10),
                self._build_options(),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            self.confetti_layer
        ], expand=True)

    async def run(self):
        """Flujo principal del ejercicio."""
        self._reset()
        op = self.visual_setup["operation"]
        emoji = self.visual_setup["emoji"]

        # Paso 1: Mostrar objetos iniciales
        if op in ("+", "-"):
            self.renderer.render_objects(self.objects_view, emoji, self.visual_setup["total"], self.page)
        elif op == "×":
            self.renderer.render_groups(self.objects_view, emoji, self.visual_setup["groups"], self.visual_setup["per_group"], self.page)
        elif op == "÷":
            self.renderer.render_objects(self.objects_view, emoji, self.visual_setup["total"], self.page)

        await self._wait(2000)  # ✅ 2 segundos para observar
        
        # Narrar intro
        await self.narrator.speak_and_wait(self.logic.get_narration_text("intro"))

        # Paso 2: Animación de la operación
        if op == "-":
            await self.animator.animate_remove(self.objects_view, self.visual_setup["remove"], self.page)
        elif op == "+":
            await self.animator.animate_add(self.objects_view, emoji, self.visual_setup["add"], self.page)
        elif op == "×":
            await self.animator.animate_multiply(self.objects_view, self.page)
        elif op == "÷":
            # ✅ UNA SOLA LLAMADA (antes había dos)
            divisor = self.visual_setup.get("divisor") or self.visual_setup.get("groups", 2)
            await self.animator.animate_divide(self.objects_view, emoji, divisor, self.page)

        # Narrar acción
        await self.narrator.speak_and_wait(self.logic.get_narration_text("action"))
        
        # Narrar pregunta
        await self.narrator.speak_and_wait(self.logic.get_narration_text("question"))

    def _reset(self):
        self.objects_view.controls = []
        self.feedback.value = ""
        self.subtitle.value = ""
        self.confetti_layer.controls = []
        self.page.update()

    def _build_options(self) -> ft.Control:
        options_control = self.ui_builder.build_options(self.visual_setup["options"], self._check)
        # Ocultar botón de micrófono
        if options_control.controls:
            mic_btn = options_control.controls[-1]
            mic_btn.visible = False
        return options_control

    def _check(self, value: int):
        result = self.logic.check_answer(value)
        if result["is_correct"]:
            self.feedback.value = get_text(self.lang, "very_good")
            self.feedback.color = ft.Colors.GREEN
            self.ui_builder.launch_confetti(self.confetti_layer, self.page)
            self.page.run_task(self.ui_builder.clear_confetti, self.confetti_layer, self.page)
            self.page.run_task(self.narrator.speak_and_wait, f"{get_text(self.lang, 'very_good').replace('⭐', '').strip()} {result['correct_answer']}.")
            self.on_finish(success=True, stars=1)
        else:
            self.feedback.value = get_text(self.lang, "try_again")
            self.feedback.color = ft.Colors.ORANGE
            self.page.run_task(self.narrator.speak_and_wait, get_text(self.lang, "almost"))
            self.on_finish(success=False, stars=0)

    def _start_listening(self, e):
        self.feedback.value = "🎤 Voz no disponible en esta versión"
        self.feedback.color = ft.Colors.ORANGE
        self.page.update()

    def _on_voice_result(self, text: str):
        self.feedback.value = ""
        number = text_to_number(text, self.lang)
        if number is not None:
            self.subtitle.value = f'Dijiste: "{text}" ({number})'
            self._check(number)
        else:
            self.subtitle.value = f'Dijiste: "{text}"'
            self.feedback.value = "🤔 No entendí el número. ¡Intenta de nuevo!"
            self.feedback.color = ft.Colors.ORANGE
            self.page.update()

    def _on_voice_error(self, error: str):
        self.feedback.value = ""
        error_messages = {
            "not_supported": "Tu navegador no soporta voz",
            "no-speech": "No se detectó voz",
            "audio-capture": "No se encontró el micrófono",
            "network": "Error de red"
        }
        msg = error_messages.get(error, "Error en el reconocimiento")
        self.feedback.value = f"⚠️ {msg}"
        self.feedback.color = ft.Colors.RED
        self.page.update()

    def _on_voice_timeout(self):
        self.feedback.value = "⏰ Se acabó el tiempo. ¡Intenta de nuevo!"
        self.feedback.color = ft.Colors.ORANGE
        self.page.update()

    def _show_subtitle(self, text: str):
        self.subtitle.value = f'"{text}"'
        self.page.update()

    async def _wait(self, ms: int):
        """Espera milisegundos."""
        await asyncio.sleep(ms / 1000)  # ✅ CORREGIDO: era ms / 5000

# """
# core/engine.py
# COORDINADOR PRINCIPAL.
# Solo orquesta los módulos especializados.
# """
# import asyncio
# import flet as ft
# from core.game_logic import GameLogic
# from core.narrator import Narrator
# from core.speech import SpeechService
# from core.number_parser import text_to_number
# from core.visual_renderer import VisualRenderer
# from core.animator import Animator
# from core.ui_builder import UIBuilder
# from core.translations import get_text


# class ActivityEngine:
#     """
#     CAPA 2: COORDINADOR.
#     Orquesta: GameLogic (lógica), VisualRenderer (dibujo), Animator (animaciones),
#     UIBuilder (UI), SpeechService (voz), Narrator (audio).
#     """

#     def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
#         self.page = page
#         self.on_finish = on_finish
#         self.lang = lang
        
#         # 1. Motor Puro (Capa 1)
#         self.logic = GameLogic(activity, lang)
#         self.visual_setup = self.logic.get_visual_setup()
        
#         # 2. Módulos Especializados (Capa 2)
#         self.renderer = VisualRenderer()
#         self.animator = Animator(self.renderer)
#         self.ui_builder = UIBuilder()
        
#         self.narrator = Narrator(lang=lang, on_text=self._show_subtitle)
#         self.narrator.set_page(page)
        
#         self.speech_service = SpeechService(page, lang=lang)
#         self.speech_service.on_result = self._on_voice_result
#         self.speech_service.on_error = self._on_voice_error
#         self.speech_service.on_timeout = self._on_voice_timeout

#         # 3. Elementos de la Interfaz
#         self.subtitle = ft.Text(
#             "", 
#             size=26,
#             weight=ft.FontWeight.NORMAL,
#             color=ft.Colors.BLUE_GREY_700, 
#             text_align=ft.TextAlign.CENTER, 
#             width=600,
#             italic=True
#         )
#         self.objects_view = ft.Column(
#             wrap=False,
#             spacing=8,
#             horizontal_alignment=ft.CrossAxisAlignment.CENTER
#         )
#         self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
#         self.confetti_layer = ft.Stack(expand=True)

#     def build(self) -> ft.Control:
#         """Construye la vista principal."""
#         return ft.Stack([
#             ft.Column([
#                 ft.Text(self.logic.get_title(), size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
#                 ft.Container(height=20),
#                 self.objects_view,
#                 ft.Container(height=20),
#                 self.subtitle,
#                 self.feedback,
#                 ft.Container(height=10),
#                 self._build_options(),
#             ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
#             self.confetti_layer
#         ], expand=True)

#     async def run(self):
#         """Flujo principal del ejercicio."""
#         self._reset()
#         op = self.visual_setup["operation"]
#         emoji = self.visual_setup["emoji"]

#         # Paso 1: Mostrar objetos iniciales
#         if op in ("+", "-"):
#             self.renderer.render_objects(self.objects_view, emoji, self.visual_setup["total"], self.page)
#         elif op == "×":
#             self.renderer.render_groups(self.objects_view, emoji, self.visual_setup["groups"], self.visual_setup["per_group"], self.page)
#         elif op == "÷":
#             self.renderer.render_objects(self.objects_view, emoji, self.visual_setup["total"], self.page)

#         # Esperar para que el niño observe
#         await self._wait(2000)
        
#         # Narrar intro
#         await self.narrator.speak_and_wait(self.logic.get_narration_text("intro"))

#         # Paso 2: Animación de la operación
#         if op == "-":
#             await self.animator.animate_remove(self.objects_view, self.visual_setup["remove"], self.page)
#         elif op == "+":
#             await self.animator.animate_add(self.objects_view, emoji, self.visual_setup["add"], self.page)
#         elif op == "×":
#             await self.animator.animate_multiply(self.objects_view, self.page)
#         elif op == "÷":
#             # ✅ CORREGIDO: Solo una llamada a animate_divide
#             divisor = self.visual_setup.get("divisor") or self.visual_setup.get("groups", 2)
#             await self.animator.animate_divide(self.objects_view, emoji, divisor, self.page)

#         # Narrar acción
#         await self.narrator.speak_and_wait(self.logic.get_narration_text("action"))
        
#         # Narrar pregunta
#         await self.narrator.speak_and_wait(self.logic.get_narration_text("question"))

#     def _reset(self):
#         """Limpia la vista para el siguiente ejercicio."""
#         self.objects_view.controls = []
#         self.feedback.value = ""
#         self.subtitle.value = ""
#         self.confetti_layer.controls = []
#         self.page.update()

#     def _build_options(self) -> ft.Control:
#         """Construye los botones de respuesta."""
#         options_control = self.ui_builder.build_options(self.visual_setup["options"], self._check)
        
#         # Ocultar botón de micrófono (flet-audio-recorder no compatible)
#         if options_control.controls:
#             mic_btn = options_control.controls[-1]
#             mic_btn.visible = False
        
#         return options_control

#     def _check(self, value: int):
#         """Valida la respuesta usando el Motor Puro."""
#         result = self.logic.check_answer(value)
        
#         if result["is_correct"]:
#             self.feedback.value = get_text(self.lang, "very_good")
#             self.feedback.color = ft.Colors.GREEN
#             self.ui_builder.launch_confetti(self.confetti_layer, self.page)
#             self.page.run_task(self.ui_builder.clear_confetti, self.confetti_layer, self.page)
#             self.page.run_task(self.narrator.speak_and_wait, f"{get_text(self.lang, 'very_good').replace('⭐', '').strip()} {result['correct_answer']}.")
#             self.on_finish(success=True, stars=1)
#         else:
#             self.feedback.value = get_text(self.lang, "try_again")
#             self.feedback.color = ft.Colors.ORANGE
#             self.page.run_task(self.narrator.speak_and_wait, get_text(self.lang, "almost"))
#             self.on_finish(success=False, stars=0)

#     def _start_listening(self, e):
#         """Inicia el reconocimiento de voz (desactivado)."""
#         self.feedback.value = "️ Voz no disponible en esta versión"
#         self.feedback.color = ft.Colors.ORANGE
#         self.page.update()

#     def _on_voice_result(self, text: str):
#         """Procesa el texto reconocido."""
#         self.feedback.value = ""
#         number = text_to_number(text, self.lang)
        
#         if number is not None:
#             self.subtitle.value = f'Dijiste: "{text}" ({number})'
#             self._check(number)
#         else:
#             self.subtitle.value = f'Dijiste: "{text}"'
#             self.feedback.value = "🤔 No entendí el número. ¡Intenta de nuevo!"
#             self.feedback.color = ft.Colors.ORANGE
#             self.page.update()

#     def _on_voice_error(self, error: str):
#         """Maneja errores del reconocimiento de voz."""
#         self.feedback.value = ""
#         error_messages = {
#             "not_supported": "Tu navegador no soporta voz",
#             "no-speech": "No se detectó voz",
#             "audio-capture": "No se encontró el micrófono",
#             "network": "Error de red"
#         }
#         msg = error_messages.get(error, "Error en el reconocimiento")
#         self.feedback.value = f"⚠️ {msg}"
#         self.feedback.color = ft.Colors.RED
#         self.page.update()

#     def _on_voice_timeout(self):
#         """Maneja el timeout del reconocimiento de voz."""
#         self.feedback.value = " Se acabó el tiempo. ¡Intenta de nuevo!"
#         self.feedback.color = ft.Colors.ORANGE
#         self.page.update()

#     def _show_subtitle(self, text: str):
#         """Muestra el subtítulo de la narración."""
#         self.subtitle.value = f'"{text}"'
#         self.page.update()

#     async def _wait(self, ms: int):
#         """Espera milisegundos."""
#         await asyncio.sleep(ms / 1000)  # ✅ CORREGIDO: era ms / 5000