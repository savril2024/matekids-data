import asyncio
import flet as ft
import json
import random
from pathlib import Path

from core.engine import ActivityEngine
from core import users
from core.pdf_generator import PDFGenerator
from core.translations import get_text

BASE_DIR = Path(__file__).resolve().parent
ACTIVITIES_FILE = BASE_DIR / "data" / "activities.json"


def load_activities() -> list:
    if not ACTIVITIES_FILE.exists():
        print(f"⚠️ No se encontró {ACTIVITIES_FILE}")
        return []
    try:
        data = json.loads(ACTIVITIES_FILE.read_text(encoding="utf-8"))
        return data.get("activities", [])
    except Exception as e:
        print(f"⚠️ ERROR: {e}")
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
    page.title = "MateKids 🧮"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.VerticalAlignment.CENTER
    page.padding = 20
    
    if hasattr(page, 'window'):
        page.window.width = 900
        page.window.height = 700

    current_user = None
    current_level = 1
    score = 0
    activities_done = 0
    MAX_PER_SESSION = 5
    current_lang = "es"

    # ========== LOGIN ==========
    selected_avatar = users.AVATARS[0]
    avatar_buttons = []

    def on_avatar_pick(e, selected: str):
        nonlocal selected_avatar
        selected_avatar = selected
        for btn in avatar_buttons:
            btn.bgcolor = ft.Colors.YELLOW_200 if getattr(btn, '_avatar', '') == selected_avatar else ft.Colors.GREY_200
        page.update()

    avatar_grid = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    for i, a in enumerate(users.AVATARS):
        avatar_container = ft.Container(
            content=ft.Text(a, size=40),
            width=70,
            height=70,
            alignment=ft.Alignment(0, 0),
            bgcolor=ft.Colors.YELLOW_200 if i == 0 else ft.Colors.GREY_200,
            border_radius=20,
            ink=True,
            on_click=lambda e, avatar=a: on_avatar_pick(e, avatar)
        )
        avatar_container._avatar = a
        avatar_buttons.append(avatar_container)
        avatar_grid.controls.append(avatar_container)

    name_field = ft.TextField(
        label=get_text(current_lang, "your_name"), 
        text_size=22, 
        width=350, 
        text_align=ft.TextAlign.CENTER, 
        border_radius=20
    )

    def update_language(lang: str):
        nonlocal current_lang
        current_lang = lang
        name_field.label = get_text(current_lang, "your_name")
        login_welcome.value = get_text(current_lang, "welcome")
        login_choose_avatar.value = get_text(current_lang, "choose_avatar")
        login_start_btn.content.value = get_text(current_lang, "start_playing")
        page.update()

    lang_flag = ft.Text("🇧", size=20)
    lang_text_label = ft.Text("EN", size=16, weight=ft.FontWeight.BOLD)

    def toggle_language(e):
        nonlocal current_lang
        current_lang = "en" if current_lang == "es" else "es"
        lang_flag.value = "🇪🇸" if current_lang == "es" else "🇬🇧"
        lang_text_label.value = "ES" if current_lang == "es" else "EN"
        update_language(current_lang)

    lang_btn = ft.Container(
        content=ft.Button(
            content=ft.Row([lang_flag, lang_text_label], spacing=5),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=15),
            ),
            on_click=toggle_language,
        ),
        padding=ft.Padding(top=10, right=10, bottom=0, left=0),
    )
    
    def do_login(e):
        nonlocal current_user
        name = name_field.value.strip()
        if not name:
            name_field.error_text = get_text(current_lang, "name_required")
            page.update()
            return
        current_user = users.create_user(name, selected_avatar, current_lang)
        show_home()

    login_welcome = ft.Text(get_text(current_lang, "welcome"), size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO)
    login_choose_avatar = ft.Text(get_text(current_lang, "choose_avatar"), size=20)
    login_start_btn = rounded_button(get_text(current_lang, "start_playing"), ft.Colors.GREEN, 280, 60, do_login, text_size=22)

    login_view = ft.Column([
        login_welcome,
        login_choose_avatar,
        avatar_grid,
        ft.Container(height=20),
        ft.Row([lang_btn], alignment=ft.MainAxisAlignment.END),
        ft.Container(height=10),
        name_field,
        ft.Container(height=10),
        login_start_btn
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    # ========== HOME ==========
    home_title = ft.Text("", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO)
    stars_label = ft.Text("", size=22)
    pdf_status = ft.Text("", size=16, color=ft.Colors.GREEN)

    def pick_level(lvl: int):
        nonlocal current_level, score, activities_done
        current_level = lvl
        score = 0
        activities_done = 0
        show_game()

    
    async def generate_pdf(e):
       # Genera y descarga el cuadernillo como PNG.
        try:
            from core.pdf_generator import PDFGenerator
            
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            output_path = (
            BASE_DIR
            / "data"
            / f"cuadernillo_nivel_{current_level}_{current_lang}.png"
            )

            
            # 1. Generar el archivo en assets/downloads/
            generated_path = generator.generate_workbook(current_level, output_path, current_lang)
            filename = generated_path.name
            
            # 2. URL relativa que Flet sirve automáticamente desde la carpeta assets/
            download_url = f"/assets/downloads/{filename}"
            print("Descargando:", download_url)
            # 3. ✅ CORREGIDO: Usar await directamente (la función ahora es async)
            await page.launch_url(download_url)

            
            # 4. Mostrar mensaje de éxito
            pdf_status.value = f"✅ ¡Listo! Abriendo: {filename}"
            pdf_status.color = ft.Colors.GREEN
            page.update()
            
        except Exception as ex:
            pdf_status.value = f"❌ Error: {ex}"
            pdf_status.color = ft.Colors.RED
            page.update()
            print(f"ERROR en generate_pdf: {ex}")      
    ##hasta aqui    

    def toggle_home_language(e):
        nonlocal current_lang
        current_lang = "en" if current_lang == "es" else "es"
        home_title.value = f"{get_text(current_lang, 'greeting')} {current_user['avatar']} {current_user['name']}!"
        stars_label.value = f" {get_text(current_lang, 'stars')}: {current_user.get('stars', 0)}"
        choose_level_text.value = get_text(current_lang, "choose_level")
        level_btns.controls[0].content.value = get_text(current_lang, "level_1")
        level_btns.controls[1].content.value = get_text(current_lang, "level_2")
        level_btns.controls[2].content.value = get_text(current_lang, "level_3")
        pdf_btn.content.value = get_text(current_lang, "generate_pdf")
        page.update()

    lang_toggle_btn = ft.IconButton(
        icon=ft.Icons.LANGUAGE,
        tooltip="Cambiar idioma",
        icon_size=30,
        on_click=toggle_home_language
    )

    choose_level_text = ft.Text(get_text(current_lang, "choose_level"), size=26, weight=ft.FontWeight.BOLD)
    level_btns = ft.Row([
        rounded_button(get_text(current_lang, "level_1"), ft.Colors.GREEN, 220, 100, lambda e, l=1: pick_level(l), text_size=22),
        rounded_button(get_text(current_lang, "level_2"), ft.Colors.BLUE, 220, 100, lambda e, l=2: pick_level(l), text_size=22),
        rounded_button(get_text(current_lang, "level_3"), ft.Colors.PURPLE, 220, 100, lambda e, l=3: pick_level(l), text_size=22),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

    pdf_btn = rounded_button(get_text(current_lang, "generate_pdf"), ft.Colors.PURPLE, 260, 60, generate_pdf, text_size=18)

    home_view = ft.Column([
        ft.Row([lang_toggle_btn], alignment=ft.MainAxisAlignment.END),
        home_title, 
        stars_label,
        ft.Container(height=30),
        choose_level_text,
        ft.Container(height=10),
        level_btns,
        ft.Container(height=20),
        pdf_btn,
        pdf_status
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        # ... (tu código existente de home_view) ...

    # ✅ NUEVO: Botón de Salir
    def do_exit(e):
        # En web, page.window.close() a veces es bloqueado por el navegador.
        # Esta es la forma más segura: limpiar la pantalla y mostrar despedida.
        page.clean()
        page.add(
            ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=80),
                ft.Text("¡Gracias por jugar!", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
                ft.Text("Ya puedes cerrar esta pestaña del navegador.", size=20, color=ft.Colors.GREY_600),
            ], 
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            expand=True)
        )
        page.update()
        
        # Intentar cerrar la ventana (funciona perfecto en Desktop, en Web depende del navegador)
        # ✅ Usar page.run_task para la coroutine window.close()
        try:
            page.run_task(page.window.close)
        except Exception:
            pass  # En web, el navegador a veces bloquea el cierre automático

    exit_btn = rounded_button(
        "Salir de la App", 
        ft.Colors.RED_400, 
        220, 
        60, 
        do_exit, 
        text_size=20
    )

    # Agrega el botón al final de tu home_view
    home_view.controls.append(ft.Container(height=30))
    home_view.controls.append(exit_btn)


    def show_home():
        home_title.value = f"{get_text(current_lang, 'greeting')} {current_user['avatar']} {current_user['name']}!"
        stars_label.value = f" {get_text(current_lang, 'stars')}: {current_user.get('stars', 0)}"
        page.clean()
        page.add(home_view)
        page.update()

    # ========== GAME ==========
    game_column = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def show_game():
        nonlocal current_level, score, activities_done
        pool = [a for a in load_activities() if a["level"] == current_level]
        if not pool:
            pdf_status.value = get_text(current_lang, "no_activities")
            page.update()
            return
            
        activity = random.choice(pool)

        def toggle_game_language(e):
            nonlocal current_lang
            current_lang = "en" if current_lang == "es" else "es"
            show_game()

        game_lang_btn = ft.IconButton(
            icon=ft.Icons.LANGUAGE,
            icon_size=25,
            tooltip="Cambiar idioma",
            on_click=toggle_game_language
        )

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
        game_column.controls = [
            ft.Row([game_lang_btn], alignment=ft.MainAxisAlignment.END),
            engine.build()
        ]

        page.clean()
        page.add(game_column)
        page.update()
        page.run_task(engine.run)

    # ========== RESULT ==========
    result_title = ft.Text("", size=38, weight=ft.FontWeight.BOLD)
    result_msg = ft.Text("", size=24)
    diploma_status = ft.Text("", size=14, color=ft.Colors.GREEN, italic=True)
    async def generate_diploma_action(e):
        # """Genera y descarga el diploma como PNG."""
        try:
            from core.pdf_generator import PDFGenerator
            generator = PDFGenerator(ACTIVITIES_FILE, BASE_DIR)
            
            safe_name = current_user["name"].replace(" ", "_").lower()
            output_path = BASE_DIR / "data" / f"diploma_nivel_{current_level}_{safe_name}_{current_lang}.png"
            # 1. Generar el archivo en assets/downloads/
            generated_path = generator.generate_diploma(
                user_name=current_user["name"],
                level=current_level,
                stars=score,
                output_path=output_path,
                lang=current_lang
            )
            
            filename = generated_path.name
             # 2. URL relativa que Flet sirve automáticamente desde la carpeta assets/
            download_url = f"/assets/downloads/{filename}"
            print("Descargando:", download_url)

            # 3. ✅ CORREGIDO: Usar await directamente
            await page.launch_url(download_url)
            # 4. Mostrar mensaje de éxito
            diploma_status.value = f"✅ ¡Diploma listo! Abriendo: {filename}"
            diploma_status.color = ft.Colors.GREEN
            page.update()
            
        except Exception as ex:
            diploma_status.value = f"❌ Error: {ex}"
            diploma_status.color = ft.Colors.RED
            page.update() 
        
    #HASTA AQUI DIPLOMA
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
        page.clean()
        page.add(result_view)
        page.update()

    def show_login():
        page.clean()
        page.add(login_view)
        page.update()

    # INICIAR
    show_login()


# ✅ BLOQUE CORRECTO PARA FLET 0.86+
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    
    ft.run(
        main,
        host="0.0.0.0",
        port=port,
        view="web_browser",
        assets_dir="assets"
    #    upload_dir="uploads",  # necesario: aqui llega el audio grabado por AudioRecorder

    )