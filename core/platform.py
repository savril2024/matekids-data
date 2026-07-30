"""
core/platform.py
CAPA DE COMPATIBILIDAD - Aísla el proyecto de cambios en Flet.
Adaptado estrictamente a la API de Flet 0.86.2.
"""
import asyncio
import flet as ft
from typing import Optional, Callable


class PlatformContext:
    def __init__(self, page: ft.Page, lang: str = "es"):
        self.page = page
        self.lang = lang
        self._web = self._detect_web()
        print(f"✅ PlatformContext: web={self._web}, lang={lang}")
    
    def _detect_web(self) -> bool:
        import os
        return (
            os.environ.get("FLET_VIEW") == "web_browser" or
            os.environ.get("FLET_PLATFORM") == "web" or
            hasattr(self.page, "session_id")
        )
    
    def is_web(self) -> bool:
        return self._web
    
    async def open_url(self, url: str, new_tab: bool = True) -> bool:
        """
        Abre una URL. En Flet 0.86.2:
        self.page.launch_url es un coroutine y debe ser esperado con await.
        """
        try:
            if new_tab:
                res = self.page.launch_url(url, web_popup_window_name="_blank", web_popup_window=True)
            else:
                res = self.page.launch_url(url)
            
            if asyncio.iscoroutine(res):
                await res
            return True
        except Exception as e:
            print(f"⚠️ open_url falló con page.launch_url: {e}")
            try:
                res = self.page.launch_url(url)
                if asyncio.iscoroutine(res):
                    await res
                return True
            except Exception as ex2:
                print(f"⚠️ open_url fallback falló: {ex2}")
                return False
    
    async def download_file(self, url: str, filename: str) -> bool:
        """
        En Flet 0.86.2 sin run_js, la forma más segura de acceder a un asset 
        generado es abrirlo en una nueva pestaña. El navegador lo mostrará 
        y el usuario puede guardarlo (Ctrl+S o mantener presionado en móvil).
        """
        return await self.open_url(url, new_tab=True)
    
    async def speak(self, text: str, lang: Optional[str] = None, 
                    on_text: Optional[Callable] = None) -> None:
        if on_text:
            on_text(text)
        
        words = len(text.split())
        wait_time = max(2.5, min(8.0, words * 0.35))
        
        print(f"[PLATFORM.speak] {text} ({wait_time:.1f}s)")
        await asyncio.sleep(wait_time)
    
    async def speech_to_text(self, lang: Optional[str] = None, 
                             timeout_ms: int = 6000) -> Optional[str]:
        print("⚠️ [PLATFORM.speech_to_text] No disponible en esta versión")
        return None
    
    async def vibrate(self, pattern: int = 100) -> None:
        # Sin run_js, la vibración no se puede disparar desde Python en Flet 0.86.2 web
        pass
    
    async def share_file(self, url: str, title: str = "", text: str = "") -> bool:
        return await self.open_url(url, new_tab=True)


_platform_instance: Optional[PlatformContext] = None

def get_platform(page: ft.Page, lang: str = "es") -> PlatformContext:
    global _platform_instance
    if _platform_instance is None or _platform_instance.page is not page:
        _platform_instance = PlatformContext(page, lang)
    return _platform_instance

def reset_platform():
    global _platform_instance
    _platform_instance = None