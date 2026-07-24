import flet as ft

def main(page: ft.Page):
    page.title = "Prueba"
    page.add(ft.Text("Flet funciona"))

ft.run(main)

# """
# debug_main.py

# Wrapper temporal de diagnóstico. No reemplaza a main.py: lo IMPORTA
# y ejecuta tu main() real dentro de un try/except.

# Por qué existe:
#   Si algo falla dentro de main(page) ANTES del primer page.update(),
#   Flet no muestra ningún error en pantalla — simplemente se queda
#   la pantalla gris en blanco, y el traceback puede quedar enterrado
#   en una consola que a veces ni se ve (ej. al abrir con doble clic
#   en Windows, o en una ventana de flet-desktop sin consola visible).

# Qué hace este archivo:
#   1. Corre tu main() real dentro de un try/except.
#   2. Si hay una excepción: la imprime en consola, la guarda en
#      debug_log.txt (junto a este archivo) Y la muestra directamente
#      en la página, en rojo, para que sea imposible no verla.
#   3. Si NO hay excepción y aun así ves la pantalla en blanco/gris,
#      eso descarta un error de Python y apunta a un problema del
#      lado del navegador/Flutter (ej. CDN bloqueado por firewall,
#      CanvasKit no carga). Dímelo y seguimos por ahí.

# Cómo usarlo:
#     py debug_main.py

# Cuando confirmemos la causa, este archivo se puede borrar —
# main.py no se modifica en ningún momento.
# """

# import os
# import sys
# import traceback
# from pathlib import Path

# import flet as ft

# BASE_DIR = Path(__file__).resolve().parent
# LOG_FILE = BASE_DIR / "debug_log.txt"

# # Importamos tu main() real sin ejecutar su "if __name__ == '__main__':"
# from main import main as real_main


# def _print_environment_info():
#     """Imprime info útil de entorno al arrancar, para descartar versiones desalineadas."""
#     print("=" * 60)
#     print("MateKids — modo diagnóstico")
#     print("=" * 60)
#     print(f"Python: {sys.version.split()[0]}")
#     try:
#         import flet as _ft
#         print(f"flet: {getattr(_ft, '__version__', '¿?')}")
#     except Exception as ex:
#         print(f"No se pudo leer la versión de flet: {ex}")
#     for pkg in ("flet_web", "flet_desktop", "flet_audio"):
#         try:
#             mod = __import__(pkg)
#             print(f"{pkg}: instalado ({getattr(mod, '__file__', '¿?')})")
#         except ImportError:
#             print(f"{pkg}: NO instalado")
#     print(f"assets_dir esperado en: {BASE_DIR / 'assets'} (existe: {(BASE_DIR / 'assets').exists()})")
#     print(f"speech.js esperado en: {BASE_DIR / 'assets' / 'js' / 'speech.js'} "
#           f"(existe: {(BASE_DIR / 'assets' / 'js' / 'speech.js').exists()})")
#     print("=" * 60)


# def safe_main(page: ft.Page):
#     try:
#         real_main(page)
#         print("✅ main(page) terminó sin lanzar ninguna excepción.")
#     except Exception:
#         tb = traceback.format_exc()

#         print("=" * 60)
#         print("❌ ERROR AL CARGAR LA APP (esto es lo que estaba causando la pantalla en blanco):")
#         print(tb)
#         print("=" * 60)

#         try:
#             LOG_FILE.write_text(tb, encoding="utf-8")
#             print(f"📝 Traceback guardado en: {LOG_FILE}")
#         except Exception as write_err:
#             print(f"⚠️ No se pudo guardar debug_log.txt: {write_err}")

#         # Mostrarlo directamente en la página, para que sea visible
#         # incluso si no hay consola a la vista.
#         page.views.clear()
#         page.views.append(
#             ft.View(
#                 "/",
#                 [
#                     ft.Container(
#                         content=ft.Column(
#                             [
#                                 ft.Text(
#                                     "⚠️ Error al cargar MateKids",
#                                     size=24,
#                                     weight=ft.FontWeight.BOLD,
#                                     color=ft.Colors.RED,
#                                 ),
#                                 ft.Text(
#                                     f"El detalle completo se guardó en: {LOG_FILE.name}",
#                                     size=14,
#                                     color=ft.Colors.GREY_700,
#                                 ),
#                                 ft.Container(
#                                     content=ft.Text(
#                                         tb,
#                                         size=12,
#                                         selectable=True,
#                                     ),
#                                     bgcolor=ft.Colors.GREY_100,
#                                     padding=15,
#                                     border_radius=8,
#                                 ),
#                             ],
#                             scroll=ft.ScrollMode.AUTO,
#                             spacing=15,
#                             expand=True,
#                         ),
#                         padding=20,
#                         expand=True,
#                     )
#                 ],
#             )
#         )
#         page.update()


# if __name__ == "__main__":
#     _print_environment_info()
#     port = int(os.environ.get("PORT", 8080))

#     # no_cdn=True: sirve CanvasKit/fuentes desde el paquete flet-web ya
#     # instalado localmente, en vez de descargarlos de un CDN externo.
#     # Si la pantalla gris se debe a que un firewall/antivirus bloquea
#     # ese CDN (síntoma típico: pestaña de navegador real, título
#     # "MateKids" visible, pero el lienzo de Flutter nunca pinta nada
#     # y no aparece ningún error de Python), esto lo resuelve.
#     print("Arrancando con no_cdn=True (CanvasKit servido localmente, no desde un CDN externo)...")
#     ft.run(
#         safe_main,
#         port=port,
#         host="0.0.0.0",
#         view=ft.AppView.WEB_BROWSER,
#         assets_dir="assets",
#         no_cdn=True,
#     )