import asyncio
import subprocess
import flet as ft
import json
import random
import sys
from pathlib import Path
from core.engine import ActivityEngine
from core import users
from core.pdf_generator import PDFGenerator
from core.translations import get_text, get_available_languages

# Ruta absoluta segura
BASE_DIR = Path(__file__).resolve().parent
ACTIVITIES_FILE = BASE_DIR / "data" / "activities.json"

def load_activities() -> list:
    if not ACTIVITIES_FILE.exists():
        print(f"⚠️ ADVERTENCIA: No se encontró {ACTIVITIES_FILE}")
        return []
    try:
        data = json.loads(ACTIVITIES_FILE.read_text(encoding="utf-8"))
        return data.get("activities", [])
    except Exception as e:
        print(f"⚠️ ERROR leyendo JSON: {e}")
        return []

def rounded_button(text_content, bgcolor, width, height, on_click, text_size=20, text_color="white"):
    return ft.Button(
        content=ft.Text(text_content, size=text_size, weight=ft.FontWeight.BOLD, color=text_color),
        width=width,
        height=height,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=20),
            bgcolor=bgcolor,
            color=text_color,
        ),
        on_click=on_click
    )

def main(page: ft.Page):
    page.title = "MateKids "
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.VerticalAlignment.CENTER
    page.padding = 20
    page.window_width = 900
    page.window_height = 700

    current_user = None
    current_level = 1
    score = 0
    activities_done = 0
    MAX_PER_SESSION = 5
    current_lang = "es"  # Idioma por defecto

    # ---------- LOGIN ----------
    selected_avatar = users.AVATARS[0]
    avatar_buttons = []

    def on_avatar_pick(e):
        nonlocal selected_avatar
        selected_avatar = e.control.data
        for btn in avatar_buttons:
            btn.bgcolor = ft.Colors.YELLOW_200 if btn.data == selected_avatar else ft.Colors.GREY_200
        page.update()

    # Selector de idioma
    lang_dropdown = ft.Dropdown(
        label="Language / Idioma",
        options=[
            ft.dropdown.Option(key="es", text="🇪🇸 Español"),
            ft.dropdown.Option(key="en", text="🇬🇧 English"),
        ],
        value="es",
        width=200,
        on_change=lambda e: update_language(e.control.value)  # <-- CAMBIO CLAVE
    )

    def update_language(lang: str):
        nonlocal current_lang
        current_lang = lang
        # Actualizar textos dinámicos
        if 'login_view' in locals():
            refresh_login_texts()
        page.update()

    avatar_grid = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    for i, a in enumerate(users.AVATARS):
        btn = ft.ElevatedButton(
            content=ft.Text(a, size=32), 
            width=70, 
            height=70, 
            data=a,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                bgcolor=ft.Colors.YELLOW_200 if i == 0 else ft.Colors.GREY_200
            ),
        )
        avatar_buttons.append(btn)
        avatar_grid.controls.append(btn)

    name_field = ft.TextField(
        label=get_text(current_lang, "your_name"), 
        text_size=22, 
        width=350, 
        text_align=ft.TextAlign.CENTER, 
        border_radius=20
    )

    def refresh_login_texts():
        """Actualiza textos del login según idioma"""
        name_field.label = get_text(current_lang, "your_name")
        login_view.controls[0].value = get_text(current_lang, "welcome")
        login_view.controls[1].value = get_text(current_lang, "choose_avatar")
        login_view.controls[5].content.value = get_text(current_lang, "start_playing")

    def do_login(e):
        nonlocal current_user
        name = name_field.value.strip()
        if not name:
            name_field.error_text = get_text(current_lang, "name_required")
            page.update()
            return
        current_user = users.create_user(name, selected_avatar, current_lang)
        show_home()

    login_view = ft.Column([
        ft.Text(get_text(current_lang, "welcome"), size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
        ft.Text(get_text(current_lang, "choose_avatar"), size=20),
        avatar_grid,
        ft.Container(height=20),
        lang_dropdown,
        ft.Container(height=10),
        name_field,
        ft.Container(height=10),
        rounded_button(get_text(current_lang, "start_playing"), ft.Colors.GREEN, 280, 60, do_login, text_size=22)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    # ---------- HOME ----------
    home_title = ft.Text("", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO)
    stars_label = ft.Text("", size=22)
    pdf_status = ft.Text("", size=16, color=ft.Colors.GREEN)

    def pick_level(lvl: int):
        nonlocal current_level, score, activities_done
        current_level = lvl
        score = 0
        activities_done = 0
        show_game()

    def generate_pdf(e):
        try:
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            output_path = BASE_DIR / "data" / f"cuadernillo_nivel_{current_level}_{current_lang}.pdf"
            generator.generate_workbook(current_level, output_path, current_lang)
            pdf_status.value = f"{get_text(current_lang, 'pdf_saved')} {output_path.name}"
            page.update()
        except Exception as ex:
            pdf_status.value = f"{get_text(current_lang, 'pdf_error')}: {ex}"
            page.update()

    home_view = ft.Column([
        home_title, 
        stars_label,
        ft.Container(height=30),
        ft.Text(get_text(current_lang, "choose_level"), size=26, weight=ft.FontWeight.BOLD),
        ft.Container(height=10),
        ft.Row([
            rounded_button(get_text(current_lang, "level_1"), ft.Colors.GREEN, 220, 100, lambda e, l=1: pick_level(l), text_size=22),
            rounded_button(get_text(current_lang, "level_2"), ft.Colors.BLUE, 220, 100, lambda e, l=2: pick_level(l), text_size=22),
            rounded_button(get_text(current_lang, "level_3"), ft.Colors.PURPLE, 220, 100, lambda e, l=3: pick_level(l), text_size=22),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Container(height=20),
        rounded_button(get_text(current_lang, "generate_pdf"), ft.Colors.PURPLE, 260, 60, generate_pdf, text_size=18),
        pdf_status
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def show_home():
        home_title.value = f"{get_text(current_lang, 'greeting')} {current_user['avatar']} {current_user['name']}!"
        stars_label.value = f" {get_text(current_lang, 'stars')}: {current_user.get('stars', 0)}"
        page.views.clear()
        page.views.append(ft.View("/", [home_view]))
        page.update()

    # ---------- GAME ----------
    game_column = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    game_view = ft.View("/game", [game_column], horizontal_alignment=ft.CrossAxisAlignment.CENTER, vertical_alignment=ft.VerticalAlignment.CENTER)

    def show_game():
        pool = [a for a in load_activities() if a["level"] == current_level]
        if not pool:
            pdf_status.value = get_text(current_lang, "no_activities")
            page.update()
            return
            
        activity = random.choice(pool)

        def on_finish(success: bool, stars: int):
            nonlocal score, activities_done
            if success:
                score += stars
                users.add_stars(current_user["name"], stars)
            activities_done += 1
            page.run_task(next_activity)

        async def next_activity():
            await asyncio.sleep(2)
            if activities_done >= MAX_PER_SESSION:
                show_result()
            else:
                show_game()

        engine = ActivityEngine(page, activity, on_finish, current_lang)
        game_column.controls = [engine.build()]
        page.views.clear()
        page.views.append(game_view)
        page.update()
        page.run_task(engine.run)

    # ---------- RESULT ----------
    result_title = ft.Text("", size=38, weight=ft.FontWeight.BOLD)
    result_msg = ft.Text("", size=24)
    diploma_status = ft.Text("", size=14, color=ft.Colors.GREEN, italic=True)

    def generate_diploma_action(e):
        try:
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            safe_name = current_user["name"].replace(" ", "_").lower()
            output_path = BASE_DIR / "data" / f"diploma_nivel_{current_level}_{safe_name}_{current_lang}.pdf"
            
            generator.generate_diploma(
                user_name=current_user["name"],
                level=current_level,
                stars=score,
                output_path=output_path,
                lang=current_lang
            )
            diploma_status.value = f"{get_text(current_lang, 'diploma_saved')} {output_path.name}!"
            page.update()
        except Exception as ex:
            diploma_status.value = f"{get_text(current_lang, 'diploma_error')}: {ex}"
            page.update()

    result_view = ft.Column([
        result_title, 
        result_msg,
        ft.Container(height=20),
        rounded_button(get_text(current_lang, "generate_diploma"), ft.Colors.AMBER, 280, 60, generate_diploma_action, text_size=20),
        diploma_status,
        ft.Container(height=10),
        rounded_button(get_text(current_lang, "back_home"), ft.Colors.INDIGO, 260, 60, lambda e: show_home(), text_size=20),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def show_result():
        if score >= 3:
            result_title.value = f"{get_text(current_lang, 'congratulations')} {current_user['avatar']}!"
            result_title.color = ft.Colors.AMBER
        else:
            result_title.value = f"{get_text(current_lang, 'good_job')} {current_user['avatar']}!"
            result_title.color = ft.Colors.INDIGO
            
        result_msg.value = f"{get_text(current_lang, 'got_stars')} {score} {get_text(current_lang, 'stars_in_level')} {current_level}."
        diploma_status.value = ""
        
        page.views.clear()
        page.views.append(ft.View("/result", [result_view]))
        page.update()

    def show_login():
        page.views.clear()
        page.views.append(ft.View("/", [login_view]))
        page.update()

    # ---------- Inicio ----------
    show_login()
# ============================================================
# 6. PUNTO DE ENTRADA
# ============================================================
import os
if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 8550))
    ES_RENDER = os.environ.get("RENDER", "").lower() == "true"

    if ES_RENDER:
        print("🚀 Modo Render.com activado")
        print(f"📡 Puerto: {PORT}")
        print("🌍 Audio: Web Speech API del navegador")
    else:
        print("=" * 60)
        print("🖥️  Modo LOCAL (tu PC)")
        print(f"📱 Acceso local: http://localhost:{PORT}")
        print("=" * 60)
    try:    
       pass
    except Exception:
       pass
    

    # Usamos ft.app, NO ft.run
    ft.app(
        target=main,
        port=PORT,
        host="0.0.0.0",  # Vital para que Render lo detecte
        view=ft.WEB_BROWSER
    )
  