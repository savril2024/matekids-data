"""
core/game_logic.py
MOTOR EDUCATIVO PURO. 
No importa Flet, no conoce la UI, no sabe nada de PDFs ni de audio.
Su única responsabilidad es la lógica matemática, niveles y validación.
"""

class GameLogic:
    def __init__(self, activity: dict, lang: str = "es"):
        self.activity = activity
        self.lang = lang
        self.narration = self._get_narration()

    def _get_narration(self) -> dict:
        """Extrae la narración en el idioma correcto."""
        n = self.activity.get("narration", {})
        if isinstance(n, dict) and self.lang in n:
            return n[self.lang]
        return n.get("es", {}) if isinstance(n, dict) else n

    def get_title(self) -> str:
        """Devuelve el título en el idioma actual."""
        t = self.activity.get("title", "")
        if isinstance(t, dict):
            return t.get(self.lang, t.get("es", ""))
        return t

    def get_narration_text(self, step: str) -> str:
        """Devuelve el texto a narrar según el paso (intro, action, question)."""
        return self.narration.get(step, "")

    def check_division_valid(self, total: int, divisor: int) -> bool:
       # """Verifica que la división sea exacta."""
        return total % divisor == 0


    def get_visual_setup(self) -> dict:
        """
        Devuelve QUÉ debe dibujar la UI. 
        No dice CÓMO dibujarlo (eso es trabajo de Flet).
        """
        op = self.activity["operation"]
        setup = {
            "operation": op,
            "emoji": self.activity["emoji"],
            "answer": self.activity["answer"],
            "options": self.activity["options"]
        }
        
        if op in ("+", "-"):
            setup["total"] = self.activity["total"]
            if op == "-": setup["remove"] = self.activity["remove"]
            if op == "+": setup["add"] = self.activity["add"]
        elif op == "×":
            setup["groups"] = self.activity["groups"]
            setup["per_group"] = self.activity["per_group"]
        elif op == "÷":
            # ✅ CORREGIDO: Mapear correctamente para división
            setup["total"] = self.activity["total"]
            # Soporta tanto "divisor" como "groups" en el JSON
            setup["divisor"] = self.activity.get("divisor") or self.activity.get("groups", 2)
            
            
        return setup

    def check_answer(self, user_value: int) -> dict:
        """
        Valida la respuesta del niño. 
        Devuelve un diccionario con el resultado, sin UI.
        """
        is_correct = user_value == self.activity["answer"]
        return {
            "is_correct": is_correct,
            "correct_answer": self.activity["answer"],
            "message": "¡Muy bien!" if is_correct else "Intenta otra vez"
        }

    