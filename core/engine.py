import asyncio
import flet as ft
import random
from core.narrator import Narrator
from core.translations import get_text

class ActivityEngine:
    """Motor ciego al contenido. Solo consume un dict con la actividad."""

    def __init__(self, page: ft.Page, activity: dict, on_finish, lang: str = "es"):
        self.page = page
        self.data = activity
        self.on_finish = on_finish
        self.lang = lang

        # 🔊 Audio oculto que reproduce en el navegador
        self.audio = ft.Audio(
            src="",
            autoplay=False,
            on_loaded=lambda _: None,
        )
        page.overlay.append(self.audio)

        self.narrator = Narrator(
            lang=lang,  # <-- Pasar idioma al narrador
            audio_control=self.audio,
            on_text=self._show_subtitle
        )

        self.subtitle = ft.Text("", size=22, italic=True,
                                color=ft.Colors.BLUE_GREY_700,
                                text_align=ft.TextAlign.CENTER,
                                width=600)
        self.objects_view = ft.Row(wrap=True, spacing=8,
                                   alignment=ft.MainAxisAlignment.CENTER)
        self.feedback = ft.Text("", size=36, weight=ft.FontWeight.BOLD)
        self.confetti_layer = ft.Stack(expand=True)

    def build(self) -> ft.Control:
        # Manejo seguro del título bilingüe
        title_text = self.data["title"]
        if isinstance(title_text, dict):
            title_text = title_text.get(self.lang, title_text.get("es", ""))

        return ft.Stack([
            ft.Column([
                ft.Text(title_text, size=34,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.INDIGO),
                ft.Container(height=20),
                self.objects_view,
                ft.Container(height=20),
                self.subtitle,
                self.feedback,
                ft.Container(height=10),
                self._build_options(),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               expand=True),
            self.confetti_layer
        ], expand=True)

    async def run(self):
        self._reset()
        op = self.data["operation"]

        # Manejo seguro de la narración bilingüe
        narration = self.data["narration"]
        if isinstance(narration, dict) and self.lang in narration:
            narration = narration[self.lang]
        elif isinstance(narration, dict) and "es" in narration:
            narration = narration["es"]

        # Paso 1: presentación
        if op in ("+", "-"):
            self._render_objects(self.data["total"])
        elif op == "×":
            self._render_groups(self.data["groups"], self.data["per_group"])
        elif op == "÷":
            self._render_objects(self.data["total"])

        await self._wait(300)
        await self._speak(narration.get("intro", ""))
        await self._wait(500)

        # Paso 2: animación de la operación
        if op == "-":
            await self._animate_remove(self.data["remove"])
        elif op == "+":
            await self._animate_add(self.data["add"])
        elif op == "×":
            await self._animate_multiply()
        elif op == "÷":
            await self._animate_divide(self.data["divisor"])

        await self._speak(narration.get("action", ""))
        await self._wait(400)

        # Paso 3: pregunta
        await self._speak(narration.get("question", ""))

    # ---------- Render ----------

    def _reset(self):
        self.objects_view.controls = []
        self.feedback.value = ""
        self.subtitle.value = ""
        self.confetti_layer.controls = []
        self.page.update()

    def _make_emoji(self, emoji: str, size: int = 48) -> ft.Text:
        return ft.Text(emoji, size=size,
                       animate_opacity=ft.Animation(400),
                       animate_scale=ft.Animation(400),
                       animate_offset=ft.Animation(500))
    
    def _render_objects(self, count: int):
        """Renderiza objetos agrupados en decenas y unidades para números >= 10."""
        self.objects_view.controls = []
        
        if count < 10:
            # Menos de 10: mostrar individualmente
            self.objects_view.controls = [
                self._make_emoji(self.data["emoji"]) for _ in range(count)
            ]
        else:
            # 10 o más: agrupar en decenas y unidades
            tens = count // 10  # Número de decenas
            units = count % 10  # Unidades restantes
            
            # Crear contenedor principal
            main_container = ft.Row(
                wrap=True, 
                spacing=10, 
                alignment=ft.MainAxisAlignment.CENTER
            )
            
            # Agregar grupos de decenas
            for i in range(tens):
                # Caja que representa una decena
                ten_group = ft.Container(
                    content=ft.Row(
                        [self._make_emoji(self.data["emoji"], size=32) for _ in range(10)],
                        spacing=2,
                        wrap=True
                    ),
                    border=ft.border.all(2, ft.Colors.BLUE),
                    border_radius=10,
                    padding=8,
                    bgcolor=ft.Colors.BLUE_50,
                    tooltip=f"Decena {i+1}"
                )
                main_container.controls.append(ten_group)
            
            # Agregar unidades sueltas (si hay)
            if units > 0:
                units_container = ft.Container(
                    content=ft.Row(
                        [self._make_emoji(self.data["emoji"], size=32) for _ in range(units)],
                        spacing=2
                    ),
                    border=ft.border.all(2, ft.Colors.ORANGE),
                    border_radius=10,
                    padding=8,
                    bgcolor=ft.Colors.ORANGE_50,
                    tooltip=f"{units} unidades"
                )
                main_container.controls.append(units_container)
            
            self.objects_view.controls.append(main_container)
        
        self.page.update()
    

    def _render_groups(self, groups: int, per_group: int):
        """Renderiza grupos para multiplicación (ya agrupados visualmente)."""
        self.objects_view.controls = []
        
        for i in range(groups):
            # Cada grupo es una caja con border
            group_container = ft.Container(
                content=ft.Row(
                    [self._make_emoji(self.data["emoji"], size=35) for _ in range(per_group)],
                    spacing=3,
                    wrap=True
                ),
                border=ft.border.all(2, ft.Colors.GREEN),
                border_radius=10,
                padding=8,
                bgcolor=ft.Colors.GREEN_50,
                tooltip=f"Grupo {i+1}"
            )
            self.objects_view.controls.append(group_container)
        
        self.page.update()

    async def _animate_divide(self, divisor: int):
        """Animación de división: repartir en grupos."""
        total = self.data["total"]
        
        # Crear contenedores vacíos para cada grupo
        self.objects_view.controls = []
        for i in range(divisor):
            group = ft.Container(
                content=ft.Row(spacing=3, wrap=True),
                border=ft.border.all(2, ft.Colors.PURPLE),
                border_radius=10,
                padding=8,
                bgcolor=ft.Colors.PURPLE_50,
                width=80,
                height=100,
                tooltip=f"Grupo {i+1}"
            )
            self.objects_view.controls.append(group)
        self.page.update()

        # Crear todos los objetos
        objs = [self._make_emoji(self.data["emoji"]) for _ in range(total)]
        
        # Distribuir uno por uno
        for i, obj in enumerate(objs):
            group_idx = i % divisor
            group_container = self.objects_view.controls[group_idx]
            if isinstance(group_container.content, ft.Container):
                group_container.content.controls.append(obj)
            else:
                group_container.controls.append(obj)
            self.page.update()
            await self._wait(150)


    # ---------- Animaciones ----------

    async def _animate_remove(self, n: int):
        controls = self.objects_view.controls
        to_remove = controls[-n:]
        for obj in to_remove:
            obj.opacity = 0.2
            obj.scale = 0.4
            self.page.update()
            await self._wait(200)

    async def _animate_add(self, n: int):
        for _ in range(n):
            new_obj = self._make_emoji(self.data["emoji"])
            new_obj.scale = 0
            self.objects_view.controls.append(new_obj)
            self.page.update()
            await self._wait(50)
            new_obj.scale = 1
            self.page.update()
            await self._wait(250)

    async def _animate_multiply(self):
        for group in self.objects_view.controls:
            for obj in group.controls:
                obj.scale = 1.3
            self.page.update()
            await self._wait(350)
            for obj in group.controls:
                obj.scale = 1
            self.page.update()

    async def _animate_divide(self, divisor: int):
        total = len(self.objects_view.controls)
        per_group = total // divisor
        self.objects_view.controls = []
        for _ in range(divisor):
            group = ft.Row(spacing=4)
            self.objects_view.controls.append(group)
        self.page.update()

        objs = [self._make_emoji(self.data["emoji"]) for _ in range(total)]
        for i, obj in enumerate(objs):
            group_idx = i % divisor
            self.objects_view.controls[group_idx].controls.append(obj)
            self.page.update()
            await self._wait(120)

    # ---------- UI de respuesta ----------

    def _build_options(self) -> ft.Control:
        row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        for opt in self.data["options"]:
            row.controls.append(
                ft.Button(
                    content=ft.Text(str(opt), size=34, weight=ft.FontWeight.BOLD),
                    width=90, 
                    height=90,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=20),
                        bgcolor=ft.Colors.BLUE_100,
                        color=ft.Colors.BLACK,
                    ),
                    on_click=lambda e, v=opt: self._check(v)
                )
            )
        return row

    def _check(self, value: int):
        correct = value == self.data["answer"]
        if correct:
            self.feedback.value = get_text(self.lang, "very_good")
            self.feedback.color = ft.Colors.GREEN
            self._launch_confetti()
            self.narrator.speak(
                f"{get_text(self.lang, 'very_good').replace('⭐', '').strip()} {self.data['answer']}.")
            self.on_finish(success=True, stars=1)
        else:
            self.feedback.value = get_text(self.lang, "try_again")
            self.feedback.color = ft.Colors.ORANGE
            self.narrator.speak(get_text(self.lang, "almost"))
            self.on_finish(success=False, stars=0)

    # ---------- Confeti ----------

    def _launch_confetti(self):
        emojis = ["🎉", "⭐", "", "✨", "🌟"]
        for i in range(15):
            e = ft.Text(random.choice(emojis), size=32,
                        top=-50, left=random.randint(20, 500),
                        animate_offset=ft.Animation(1200),
                        animate_opacity=ft.Animation(1200))
            self.confetti_layer.controls.append(e)
        self.page.update()

        for c in self.confetti_layer.controls:
            c.offset = ft.transform.Offset(0, 15)
            c.opacity = 0
        self.page.update()

        self.page.run_task(self._clear_confetti)

    async def _clear_confetti(self):
        await self._wait(1500)
        self.confetti_layer.controls = []
        self.page.update()

    # ---------- Helpers ----------

    def _show_subtitle(self, text: str):
        self.subtitle.value = f'"{text}"'
        self.page.update()

    async def _speak(self, text: str):
        if text:
            self.narrator.speak(text)
            await self._wait(len(text) * 70)

    async def _wait(self, ms: int):
        await asyncio.sleep(ms / 1000)