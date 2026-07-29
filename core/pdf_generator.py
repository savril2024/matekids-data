"""
core/pdf_generator.py
Genera cuadernillos y diplomas como IMÁGENES PNG con emojis a color.
En modo web, guarda en assets/downloads/ para que el navegador pueda descargar.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import os
import requests
import io
from datetime import datetime
#from core.paths import DOWNLOADS_DIR


from core.translations import get_text


class PDFGenerator:
    """Genera cuadernillos y diplomas en formato PNG con emojis a color."""
    
    def __init__(self, activities_file: Path, base_dir: Path = None):
        self.activities = self._load_activities(activities_file)
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.emoji_dir = self.base_dir / "assets" / "emojis"
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
        # ✅ NUEVO: Carpeta de descargas dentro de assets/
        self.download_dir = self.base_dir / "assets" / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_activities(self, file_path: Path) -> list:
        if not file_path.exists():
            return []
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return data.get("activities", [])
        except Exception as e:
            print(f"❌ Error cargando actividades: {e}")
            return []
    
    def _download_emoji_image(self, emoji_char: str, size: int = 40) -> Path:
        """Descarga el emoji como PNG para pegarlo en la imagen."""
        emoji_map = {
            "🍎": "1f34e", "🍕": "1f355", "🚗": "1f697", "🚕": "1f695",
            "🐟": "1f41f", "🐶": "1f436", "⭐": "2b50", "🎈": "1f388",
            "📚": "1f4da", "🎒": "1f392", "✏️": "270f-fe0f", "📐": "1f4d0",
            "🖍️": "1f58d-fe0f", "": "1f3c6", "": "1f36a", "": "1f36c",
            "🌸": "1f338", "👩‍🦰": "1f469-200d-1f9b0",
            "🍊": "1f34a", "🍇": "1f347", "🍓": "1f353", "🍒": "1f352",
            "🍑": "1f351", "🍍": "1f34d", "🥝": "1f95d", "🥑": "1f951",
            "": "1f33a", "": "1f33b", "": "1f337",
            "🐱": "1f431", "🐰": "1f430", "🐻": "1f43b", "🐼": "1f43c",
            "🦊": "1f98a", "🦁": "1f981", "🐸": "1f438", "🐦": "1f426",
            "🦋": "1f98b", "🐞": "1f41e",
            "🌙": "1f319", "☀️": "2600-fe0f", "": "1f308",
            "⚽": "26bd", "": "1f3c0", "": "1f3be",
            "": "1f682", "️": "2708-fe0f", "🚀": "1f680",
            "⛵": "26f5", "🚢": "1f6a2",
            "🏠": "1f3e0", "🏡": "1f3e1", "🏫": "1f3eb", "🏥": "1f3e5",
            "🍔": "1f354", "🍟": "1f35f", "🌭": "1f32d", "🍿": "1f37f",
            "🧁": "1f9c1", "🎂": "1f382", "🍰": "1f370",
            "🍫": "1f36b", "🍭": "1f36d", "🍡": "1f361",
            "": "1f366", "": "1f367", "": "1f368", "": "1f369",
            "🎃": "1f383", "🎄": "1f384", "🎁": "1f381", "🎀": "1f380",
            "🎉": "1f389", "🎊": "1f38a",
        }
        
        if emoji_char in emoji_map:
            code = emoji_map[emoji_char]
        elif len(emoji_char) == 1:
            code = format(ord(emoji_char), 'x')
        else:
            code = "-".join(f"{ord(c):x}" for c in emoji_char)
        
        img_path = self.emoji_dir / f"{code}_{size}.png"
        
        if not img_path.exists():
            url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{code}.png"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    img.save(img_path, "PNG")
            except Exception as e:
                print(f"⚠️ Error descargando {emoji_char}: {e}")
                return None
        return img_path if img_path.exists() else None

    def _get_font(self, size: int):
        """Obtiene una fuente del sistema."""
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except IOError:
                return ImageFont.load_default()

    def generate_workbook(self, level: int, output_path: Path, lang: str = "es") -> Path:
        """Genera el cuadernillo como imagen PNG en assets/downloads/."""
        activities = [a for a in self.activities if a["level"] == level]
        if not activities:
            raise ValueError(f"No hay actividades para el nivel {level}")
        
        # Crear lienzo (tamaño similar a A4: 1200 x 1600 px)
        width, height = 1200, 1600
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        font_title = self._get_font(60)
        font_medium = self._get_font(40)
        font_eq = self._get_font(45)

        # Encabezado colorido (barra amarilla)
        draw.rectangle([(0, 0), (width, 120)], fill=(255, 223, 0))
        title = f"{get_text(lang, 'workbook_title')} {level}"
        draw.text((width//2, 60), title, fill=(74, 20, 140), font=font_title, anchor="mm")
        
        # Campos de Nombre y Fecha
        nombre_label = "Nombre:" if lang == "es" else "Name:"
        fecha_label = "Fecha:" if lang == "es" else "Date:"
        draw.text((60, 160), f"{nombre_label} ________________________", fill=(0, 0, 0), font=font_medium)
        draw.text((650, 160), f"{fecha_label} ________________", fill=(0, 0, 0), font=font_medium)
        
        # Dibujar ejercicios
        y_offset = 260
        for i, activity in enumerate(activities[:8], 1):
            emoji_char = activity.get("emoji", "")
            operation = activity.get("operation", "+")
            
            draw.text((60, y_offset), f"{i}.", fill=(0, 0, 0), font=font_medium)
            
            emoji_img_path = self._download_emoji_image(emoji_char, size=50)
            if emoji_img_path:
                try:
                    emoji_img = Image.open(emoji_img_path).convert('RGBA')
                    img.paste(emoji_img, (120, y_offset - 10), emoji_img)
                except Exception:
                    pass
            
            eq_x = 200
            if operation == "-":
                text = f"{activity.get('total')}  -  {activity.get('remove')}  =  ______"
                color = (200, 0, 0)
            elif operation == "+":
                text = f"{activity.get('total')}  +  {activity.get('add')}  =  ______"
                color = (0, 128, 0)
            elif operation == "×":
                text = f"{activity.get('groups')}  ×  {activity.get('per_group')}  =  ______"
                color = (0, 0, 200)
            elif operation == "÷":
                text = f"{activity.get('total')}  ÷  {activity.get('divisor')}  =  ______"
                color = (128, 0, 128)
            else:
                text = "? = ______"
                color = (0, 0, 0)
            
            draw.text((eq_x, y_offset + 5), text, fill=color, font=font_eq)
            draw.line([(60, y_offset + 70), (1140, y_offset + 70)], fill=(200, 200, 200), width=2)
            y_offset += 130
        
        footer = get_text(lang, "footer")
        draw.text((width//2, height - 60), footer, fill=(100, 100, 100), font=self._get_font(30), anchor="mm")
        
        # ✅ Guardar en assets/downloads/ para que Flet lo sirva
        final_path = self.download_dir / output_path.name
        final_path = final_path.with_suffix('.png')
        img.save(str(final_path), "PNG", quality=95)
        print(f"✅ Cuadernillo generado: {final_path}")
        return final_path
    
    def generate_diploma(self, user_name: str, level: int, stars: int, output_path: Path, lang: str = "es") -> Path:
        """Genera un diploma festivo como imagen PNG de alta calidad con emojis a color."""
        width, height = 1600, 1200  # Formato horizontal (Landscape)
        
        # Fondo color crema suave para que sea cálido y amigable
        img = Image.new('RGB', (width, height), color=(255, 253, 230))
        draw = ImageDraw.Draw(img)
        
        # 1. Borde decorativo dorado doble
        draw.rectangle([(30, 30), (width-30, height-30)], outline=(255, 215, 0), width=12)
        draw.rectangle([(50, 50), (width-50, height-50)], outline=(255, 215, 0), width=4)
        
        # Esquinas decorativas (círculos dorados)
        corners = [(50, 50), (width-50, 50), (50, height-50), (width-50, height-50)]
        for cx, cy in corners:
            draw.ellipse([(cx-20, cy-20), (cx+20, cy+20)], fill=(255, 215, 0))
        
        # 2. Fuentes
        font_title = self._get_font(70)
        font_subtitle = self._get_font(35)
        font_name = self._get_font(80)
        font_text = self._get_font(40)
        font_footer = self._get_font(30)
        
        # 3. Emoji grande de Trofeo o Medalla en la parte superior
        trophy_path = self._download_emoji_image("🏆", size=120)
        if trophy_path:
            try:
                trophy_img = Image.open(trophy_path).convert('RGBA')
                # Centrar en la parte superior
                trophy_x = (width - 120) // 2
                img.paste(trophy_img, (trophy_x, 70), trophy_img)
            except Exception:
                pass
        
        # 4. Títulos
        title_text = get_text(lang, "diploma_title").upper()
        draw.text((width//2, 220), title_text, fill=(74, 20, 140), font=font_title, anchor="mm")
        
        subtitle_text = get_text(lang, "diploma_subtitle")
        draw.text((width//2, 300), subtitle_text, fill=(80, 80, 80), font=font_subtitle, anchor="mm")
        
        # 5. Nombre del niño/a (grande y destacado)
        draw.text((width//2, 420), user_name.upper(), fill=(220, 50, 50), font=font_name, anchor="mm")
        
        # Línea decorativa bajo el nombre
        draw.line([(width//2 - 200, 460), (width//2 + 200, 460)], fill=(255, 215, 0), width=6)
        
        # 6. Texto de logro con ESTRELLAS A COLOR
        level_text = get_text(lang, "completed_level")
        grade_text = get_text(lang, "with_grade")
        
        achievement_line1 = f"{level_text} {level}"
        
        draw.text((width//2, 550), achievement_line1, fill=(0, 0, 0), font=font_text, anchor="mm")
        draw.text((width//2, 600), grade_text, fill=(0, 0, 0), font=font_text, anchor="mm")
        
        # Dibujar estrellas como imágenes para que aparezcan correctamente
        star_img_path = self._download_emoji_image("⭐", size=50)
        if star_img_path:
            try:
                star_img = Image.open(star_img_path).convert('RGBA')
                # Posicionar las estrellas horizontalmente centradas
                star_x_start = (width - (stars * 55)) // 2
                for i in range(stars):
                    img.paste(star_img, (star_x_start + i * 55, 650), star_img)
            except Exception:
                pass
        
        # 7. Fecha
        if lang == "es":
            fecha = datetime.now().strftime("%d de %B de %Y")
        else:
            fecha = datetime.now().strftime("%B %d, %Y")
        draw.text((width//2, 750), f"{get_text(lang, 'date')}: {fecha}", fill=(100, 100, 100), font=font_footer, anchor="mm")
        
        # 8. Línea de firma
        draw.line([(width//2 - 150, 850), (width//2 + 150, 850)], fill=(0, 0, 0), width=3)
        draw.text((width//2, 900), get_text(lang, "teacher_signature"), fill=(0, 0, 0), font=font_footer, anchor="mm")
        
        # 9. Emoji pequeño de celebración en la esquina inferior
        party_path = self._download_emoji_image("🎉", size=60)
        if party_path:
            try:
                party_img = Image.open(party_path).convert('RGBA')
                img.paste(party_img, (80, height - 100), party_img)
                
                # Otro emoji al otro lado
                party_img2 = Image.open(party_path).convert('RGBA')
                img.paste(party_img2, (width - 140, height - 100), party_img2)
            except Exception:
                pass
        
        # 10. Guardar como PNG de alta calidad
        final_path = self.download_dir / f"diploma_{user_name.replace(' ', '_').lower()}_nivel_{level}_{lang}.png"
        img.save(str(final_path), "PNG", quality=95)
        print(f"✅ Diploma festivo generado: {final_path}")
        return final_path

    # def generate_diploma(self, user_name: str, level: int, stars: int, output_path: Path, lang: str = "es") -> Path:
    #     """Genera diploma como imagen PNG en assets/downloads/."""
    #     width, height = 1600, 1200
    #     img = Image.new('RGB', (width, height), color=(255, 255, 255))
    #     draw = ImageDraw.Draw(img)
        
    #     draw.rectangle([(20, 20), (width-20, height-20)], outline=(255, 215, 0), width=8)
    #     draw.rectangle([(40, 40), (width-40, height-40)], outline=(255, 215, 0), width=3)
        
    #     font_title = self._get_font(80)
    #     font_name = self._get_font(70)
    #     font_text = self._get_font(45)
        
    #     draw.text((width//2, 150), get_text(lang, "diploma_title"), fill=(74, 20, 140), font=font_title, anchor="mm")
    #     draw.text((width//2, 280), get_text(lang, "diploma_subtitle"), fill=(0, 0, 0), font=font_text, anchor="mm")
    #     draw.text((width//2, 450), user_name.upper(), fill=(0, 100, 0), font=font_name, anchor="mm")
        
    #     stars_text = get_text(lang, "stars_text")
    #     achievement = f"{get_text(lang, 'completed_level')} {level}\n{get_text(lang, 'with_grade')} {stars} {stars_text}."
    #     draw.multiline_text((width//2, 650), achievement, fill=(0, 0, 0), font=font_text, anchor="mm", align="center")
        
    #     final_path = self.download_dir / output_path.name
    #     final_path = final_path.with_suffix('.png')
    #     img.save(str(final_path), "PNG", quality=95)
    #     print(f"✅ Diploma generado: {final_path}")
    #     return final_path
