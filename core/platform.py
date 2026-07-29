"""
core/platform.py
CAPA DE COMPATIBILIDAD - Aísla el proyecto de cambios en Flet.

Si Flet cambia de 0.86 a 0.90 o superior, solo modificamos este archivo.
El resto del proyecto (engine, narrator, speech, main) no se entera.

API ESTABLE (no cambia aunque Flet cambie):
    - open_url(url, new_tab=True)
    - download_file(url, filename)
    - speak(text, lang="es")
    - speech_to_text(lang="es", timeout_ms=6000)
    - vibrate(pattern=100)
    - share_file(url, title, text)
    - is_web() -> bool
"""
import asyncio
import flet as ft
from typing import Optional, Callable


class PlatformContext:
    """
    Contexto de plataforma. Se inicializa UNA VEZ al arrancar la app
    y se pasa a los módulos que lo necesiten.
    """
    
    def __init__(self, page: ft.Page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self._web = self._detect_web()
        print(f" PlatformContext: web={self._web}, lang={lang}")
    
    def _detect_web(self) -> bool:
        """Detecta si estamos en modo web."""
        import os
        return (
            os.environ.get("FLET_VIEW") == "web_browser" or
            os.environ.get("FLET_PLATFORM") == "web" or
            hasattr(self.page, "session_id")
        )
    
    def is_web(self) -> bool:
        return self._web
    
    # ----------------------------------------------------------
    # NAVEGACIÓN Y DESCARGAS
    # ----------------------------------------------------------
    
    async def open_url(self, url: str, new_tab: bool = True) -> bool:
        """
        Abre una URL. En web, new_tab=True evita que la app se recargue.
        Retorna True si tuvo éxito.
        """
        try:
            # Intenta con UrlLauncher (API moderna de Flet)
            launcher = ft.UrlLauncher()
            await launcher.launch_url(url, web_popup_window=new_tab)
            return True
        except Exception as e:
            print(f"⚠️ open_url falló con UrlLauncher: {e}")
            try:
                # Fallback: run_js (si está disponible)
                if hasattr(self.page, "run_js"):
                    js = f"window.open('{url}', '_blank');"
                    await self.page.run_js(js)
                    return True
            except Exception as e2:
                print(f"⚠️ open_url falló con run_js: {e2}")
        return False
    
    async def download_file(self, url: str, filename: str) -> bool:
        """
        Fuerza la descarga de un archivo sin recargar la app.
        Usa JavaScript para crear un enlace temporal con atributo 'download'.
        """
        try:
            js = f"""
            (function() {{
                const link = document.createElement('a');
                link.href = '{url}';
                link.download = '{filename}';
                link.target = '_blank';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }})();
            """
            if hasattr(self.page, "run_js"):
                await self.page.run_js(js)
                return True
            else:
                # Fallback: abrir en nueva pestaña
                return await self.open_url(url, new_tab=True)
        except Exception as e:
            print(f"⚠️ download_file falló: {e}")
            return False
    
    # ----------------------------------------------------------
    # TEXTO A VOZ (TTS)
    # ----------------------------------------------------------
    
    async def speak(self, text: str, lang: Optional[str] = None, 
                    on_text: Optional[Callable] = None) -> None:
        """
        Narra un texto. Por defecto usa subtítulos con tiempo de lectura.
        Si en el futuro hay audio nativo, se activa aquí sin tocar el resto.
        """
        if on_text:
            on_text(text)
        
        # Calcular tiempo de lectura (~350ms por palabra, mínimo 2.5s, máximo 8s)
        words = len(text.split())
        wait_time = max(2.5, min(8.0, words * 0.35))
        
        print(f"[PLATFORM.speak] {text} ({wait_time:.1f}s)")
        await asyncio.sleep(wait_time)
    
    # ----------------------------------------------------------
    # RECONOCIMIENTO DE VOZ (STT)
    # ----------------------------------------------------------
    
    async def speech_to_text(self, lang: Optional[str] = None, 
                             timeout_ms: int = 6000) -> Optional[str]:
        """
        Escucha voz y devuelve texto.
        Actualmente deshabilitado en web (requiere Web Speech API o micrófono).
        Retorna None si no está disponible.
        """
        print("⚠️ [PLATFORM.speech_to_text] No disponible en esta versión")
        return None
    
    # ----------------------------------------------------------
    # VIBRACIÓN (móviles/tablets)
    # ----------------------------------------------------------
    
    async def vibrate(self, pattern: int = 100) -> None:
        """
        Vibra el dispositivo (solo en navegadores móviles que soporten).
        pattern: duración en ms, o lista como [100, 50, 100] para patrones.
        """
        try:
            if self._web and hasattr(self.page, "run_js"):
                if isinstance(pattern, list):
                    js_pattern = ",".join(str(p) for p in pattern)
                    js = f"navigator.vibrate([{js_pattern}]);"
                else:
                    js = f"navigator.vibrate({pattern});"
                await self.page.run_js(js)
        except Exception:
            pass  # Silencioso: la vibración es opcional
    
    # ----------------------------------------------------------
    # COMPARTIR ARCHIVOS (Web Share API)
    # ----------------------------------------------------------
    
    async def share_file(self, url: str, title: str = "", text: str = "") -> bool:
        """
        Intenta compartir usando la Web Share API del navegador.
        Fallback: abre la URL en nueva pestaña.
        """
        try:
            if self._web and hasattr(self.page, "run_js"):
                js = f"""
                (async function() {{
                    if (navigator.share) {{
                        try {{
                            await navigator.share({{
                                title: '{title}',
                                text: '{text}',
                                url: '{url}'
                            }});
                            return 'shared';
                        }} catch(e) {{
                            return 'cancelled';
                        }}
                    }}
                    return 'not_supported';
                }})();
                """
                result = await self.page.run_js(js)
                if result == "shared":
                    return True
        except Exception:
            pass
        
        # Fallback: abrir en nueva pestaña
        return await self.open_url(url, new_tab=True)


# ----------------------------------------------------------
# INSTANCIA GLOBAL (singleton por sesión)
# ----------------------------------------------------------

_platform_instance: Optional[PlatformContext] = None


def get_platform(page: ft.Page, lang: str = "es") -> PlatformContext:
    """
    Obtiene (o crea) la instancia global de PlatformContext.
    Usa esto desde cualquier módulo en lugar de instanciar directamente.
    """
    global _platform_instance
    if _platform_instance is None or _platform_instance.page is not page:
        _platform_instance = PlatformContext(page, lang)
    return _platform_instance


def reset_platform():
    """Resetea la instancia (útil en tests o al cambiar de sesión)."""
    global _platform_instance
    _platform_instance = None