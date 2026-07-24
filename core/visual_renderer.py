"""
core/visual_renderer.py
Responsable de DIBUJAR los elementos visuales.
Compatible con Flet 0.86+
"""
import flet as ft


class VisualRenderer:
    """Renderiza objetos visuales (emojis) en la interfaz."""
    
    def __init__(self):
        self.emoji_codes = {
            "🍎": "1f34e", "🍕": "1f355", "🚗": "1f697", "🚕": "1f695",
            "🐟": "1f41f", "🐶": "1f436", "⭐": "2b50", "🎈": "1f388",
            "📚": "1f4da", "🎒": "1f392", "✏️": "270f-fe0f", "📐": "1f4d0",
            "️": "1f58d-fe0f", "🏆": "1f3c6", "🍪": "1f36a", "🍬": "1f36c",
            "🌸": "1f338", "👩‍🦰": "1f469-200d-1f9b0",
        }

    def make_emoji(self, emoji: str, size: int = 35) -> ft.Image:
        """Crea una imagen SVG de Twemoji."""
        code = self.emoji_codes.get(emoji, "1f34e")
        url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/{code}.svg"
        return ft.Image(
            src=url, 
            width=size, 
            height=size, 
            fit="contain",
            animate_scale=ft.Animation(400)
        )

    def render_objects(self, objects_view: ft.Column, emoji: str, count: int, page: ft.Page):
        """
        Renderiza objetos en una Column.
        Para cantidades grandes, usa múltiples filas.
        """
        objects_view.controls.clear()
        
        if count <= 10:
            # Una sola fila
            row = ft.Row(wrap=True, spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            for _ in range(count):
                row.controls.append(self.make_emoji(emoji, size=35))
            objects_view.controls.append(row)
        else:
            # Múltiples filas para cantidades grandes
            row = ft.Row(wrap=True, spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            for i in range(count):
                row.controls.append(self.make_emoji(emoji, size=28))
                if (i + 1) % 10 == 0 and i < count - 1:
                    objects_view.controls.append(row)
                    row = ft.Row(wrap=True, spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            
            if row.controls:
                objects_view.controls.append(row)
        
        page.update()

    def render_groups(self, objects_view: ft.Column, emoji: str, groups: int, per_group: int, page: ft.Page):
        """Renderiza grupos para multiplicación."""
        objects_view.controls.clear()
        
        row = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        for _ in range(groups):
            group = ft.Container(
                content=ft.Row([self.make_emoji(emoji, size=30) for _ in range(per_group)], spacing=3, wrap=True),
                border=ft.BorderSide(width=2, color=ft.Colors.GREEN),
                border_radius=10,
                padding=8,
                bgcolor=ft.Colors.GREEN_50,
            )
            row.controls.append(group)
        
        objects_view.controls.append(row)
        page.update()