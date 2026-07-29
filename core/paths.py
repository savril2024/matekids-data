# core/paths.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "assets" / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)