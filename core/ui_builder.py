"""
core/ui_builder.py
Responsable de construir elementos de UI: botones, confeti, feedback.
"""
import random
import flet as ft
import asyncio as asyncio


class UIBuilder:
    """Construye componentes de interfaz de usuario."""
    
    @staticmethod
    def build_options(options: list, on_click_callback) -> ft.Control:
        """Construye la fila de botones numéricos + botón de micrófono."""
        col = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=15
        )
        
        # Fila de botones numéricos
        row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        for opt in options:
            row.controls.append(
                ft.Button(
                    content=ft.Text(str(opt), size=34, weight=ft.FontWeight.BOLD),
                    width=90, 
                    height=90,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=20), 
                        bgcolor=ft.Colors.BLUE_100, 
                        color=ft.Colors.BLACK
                    ),
                    on_click=lambda e, v=opt: on_click_callback(v)
                )
            )
        col.controls.append(row)
        
        # Botón de micrófono
        mic_btn = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=30),
                ft.Text("Responder con tu voz", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            width=280, 
            height=60,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=30), 
                bgcolor=ft.Colors.DEEP_PURPLE
            ),
            on_click=lambda e: None  # Se asignará después
        )
        col.controls.append(mic_btn)
        
        return col

    @staticmethod
    def launch_confetti(confetti_layer: ft.Stack, page: ft.Page):
        """Lanza animación de confeti."""
        emojis = ["🎉", "⭐", "🎊", "✨", ""]
        for _ in range(15):
            e = ft.Text(
                random.choice(emojis), 
                size=32, 
                top=-50, 
                left=random.randint(20, 500)
            )
            confetti_layer.controls.append(e)
        page.update()

    @staticmethod
    async def clear_confetti(confetti_layer: ft.Stack, page: ft.Page):
        """Limpia el confeti después de 1.5 segundos."""
        await asyncio.sleep(1.5)
        confetti_layer.controls = []
        page.update()