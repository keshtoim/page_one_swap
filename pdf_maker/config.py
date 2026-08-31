"""Хранение пользовательских настроек приложения (например, папки сохранения по умолчанию).

Настройки лежат в JSON-файле в домашней папке пользователя, чтобы не
захламлять сам проект и переживать переустановки приложения.
"""
import json
from pathlib import Path

_CONFIG_DIR = Path.home() / ".pdf_maker"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def _fallback_output_folder() -> Path:
    """Папка по умолчанию, если ничего не сохранено или сохранённая папка пропала."""
    documents = Path.home() / "Documents"
    return documents if documents.is_dir() else Path.home()


def load_output_folder() -> Path:
    """Возвращает папку для сохранения результатов, выбранную пользователем ранее,
    либо папку по умолчанию (Документы / домашняя папка), если ничего не сохранено.
    """
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        folder = Path(data.get("output_folder", ""))
        if str(folder) and folder.is_dir():
            return folder
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        pass
    return _fallback_output_folder()


def save_output_folder(folder: Path) -> None:
    """Запоминает папку для сохранения результатов, чтобы предложить её при следующем запуске."""
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(
            json.dumps({"output_folder": str(folder)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        # Не критично: если не удалось сохранить настройку, просто продолжаем работу.
        pass
